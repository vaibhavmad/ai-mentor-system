from copy import deepcopy
from typing import Dict

from policy_engine.policy_engine import PolicyEngine
from pacing_controller.enums import PacingMode
from pacing_controller.models import PacingLimits, PacingDecision
from pacing_controller.errors import TokenLimitExceededError


class PacingController:
    """
    Single enforcement authority for output pacing.

    Responsibilities:
    - Load pacing limits from PolicyEngine (single source of truth)
    - Enforce hard caps
    - Enforce multi-turn behavior for deliberative mode
    - Prevent runaway outputs

    This class NEVER:
    - Decides mode
    - Decides policy
    - Decides routing
    """

    MAX_DELIBERATIVE_TURNS = 5

    def __init__(self, policy_engine: PolicyEngine):
        """
        Initialize the pacing controller.

        - Load pacing limits from PolicyEngine
        - Validate all required modes
        - Store deep copies internally
        - Initialize deliberative state
        """
        if policy_engine is None:
            raise ValueError("PolicyEngine must be provided to PacingController")

        self._limits_by_mode: Dict[PacingMode, PacingLimits] = {}
        self.deliberative_turn_count: int = 0

        self._load_limits_from_policy(policy_engine)

    def _load_limits_from_policy(self, policy_engine: PolicyEngine) -> None:
        """
        Load and validate pacing limits from PolicyEngine.

        FAIL FAST if:
        - Any required mode is missing
        - Any required field is missing
        - Any field is malformed
        """
        required_modes = [
            PacingMode.NORMAL,
            PacingMode.CAREFUL,
            PacingMode.DELIBERATIVE,
        ]

        for mode in required_modes:
            limits = policy_engine.get_pacing_limits(mode.value)

            if limits is None:
                raise ValueError(f"Pacing limits missing for mode: {mode.value}")

            try:
                target_tokens = limits["target_tokens"]
                hard_cap_tokens = limits["hard_cap_tokens"]
                multiturn = limits["multiturn"]
            except KeyError as exc:
                raise ValueError(
                    f"Missing pacing field {exc} for mode: {mode.value}"
                ) from exc

            if not isinstance(target_tokens, int) or not isinstance(hard_cap_tokens, int):
                raise ValueError(f"Token limits must be integers for mode: {mode.value}")

            if hard_cap_tokens < target_tokens:
                raise ValueError(
                    f"Hard cap must be >= target for mode: {mode.value}"
                )

            if not isinstance(multiturn, bool):
                raise ValueError(f"'multiturn' must be boolean for mode: {mode.value}")

            self._limits_by_mode[mode] = PacingLimits(
                target_tokens=target_tokens,
                hard_cap_tokens=hard_cap_tokens,
                multiturn=multiturn,
            )

    def get_limits(self, mode: PacingMode) -> PacingLimits:
        """
        Return a DEEP COPY of pacing limits for the given mode.

        Guarantees:
        - No shared mutable state
        - No mutation leaks
        - Policy remains the single source of truth
        """
        if mode not in self._limits_by_mode:
            raise ValueError(f"Unknown pacing mode requested: {mode.value}")

        return deepcopy(self._limits_by_mode[mode])
    
    def prepare_request(self, mode: PacingMode, user_choice: str | None = None) -> dict:
        """
        Prepare LLM request constraints for the given pacing mode.

        Returns a dict containing:
        - max_tokens: hard cap enforced upstream
        - instruction_prefix: strict instructions for the LLM
        """
        limits = self.get_limits(mode)

        if mode == PacingMode.NORMAL:
            instruction = (
                "Produce a concise response.\n"
                f"Target {limits.target_tokens} tokens.\n"
                f"Hard cap {limits.hard_cap_tokens} tokens.\n"
                "Never split across turns."
            )

        elif mode == PacingMode.CAREFUL:
            instruction = (
                "Produce a detailed response.\n"
                f"Target {limits.target_tokens} tokens.\n"
                f"Hard cap {limits.hard_cap_tokens} tokens.\n"
                "Never split across turns."
            )

        elif mode == PacingMode.DELIBERATIVE:
            step_number = self.deliberative_turn_count + 1
            instruction = (
                f"This is step {step_number} of a multi-turn process.\n"
                f"Target {limits.target_tokens} tokens.\n"
                f"Hard cap {limits.hard_cap_tokens} tokens.\n"
                "If more is needed, stop and end with [CONTINUE]."
            )

        else:
            raise ValueError(f"Unsupported pacing mode: {mode}")

        return {
            "max_tokens": limits.hard_cap_tokens,
            "instruction_prefix": instruction,
        }
    
    def evaluate_output(self, mode: PacingMode, output_text: str) -> PacingDecision:
        """
        Evaluate the generated output against pacing rules.

        Decides whether the output is:
        - accepted
        - requires continuation (multi-turn)
        - rejected (hard failure)
        """
        from pacing_controller.tokenizer import estimate_tokens

        tokens = estimate_tokens(output_text)
        limits = self.get_limits(mode)

        # Hard cap enforcement (NON-RECOVERABLE)
        if tokens > limits.hard_cap_tokens:
            raise TokenLimitExceededError(
                f"Output exceeds hard cap: {tokens} > {limits.hard_cap_tokens}"
            )

        # DELIBERATIVE mode (multi-turn)
        if mode == PacingMode.DELIBERATIVE:
            if self.deliberative_turn_count >= self.MAX_DELIBERATIVE_TURNS:
                return PacingDecision(
                    accepted=True,
                    must_continue_in_next_turn=False,
                    reason="Reached max deliberative turns",
                )

            if tokens >= limits.target_tokens:
                self.deliberative_turn_count += 1
                return PacingDecision(
                    accepted=True,
                    must_continue_in_next_turn=True,
                    reason="Deliberative continuation required",
                )

            return PacingDecision(
                accepted=True,
                must_continue_in_next_turn=False,
                reason="Deliberative completed early",
            )

        # NORMAL / CAREFUL modes
        if tokens > limits.target_tokens:
            return PacingDecision(
                accepted=True,
                must_continue_in_next_turn=False,
                reason="Over target but within cap",
            )

        return PacingDecision(
            accepted=True,
            must_continue_in_next_turn=False,
            reason="Within target",
        )