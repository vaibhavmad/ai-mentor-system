from dataclasses import dataclass
from typing import Literal

from orchestrator.models import SessionState, OrchestratorContext
from pacing_controller.enums import PacingMode
from pacing_controller.controller import PacingController
from llm_executor.executor import LLMExecutor
from output_validator.validator import OutputValidator
from policy_engine.policy_engine import PolicyEngine


@dataclass(frozen=True)
class DeliberativeContinue:
    """
    Signal to the caller that deliberative execution must continue.
    Orchestrator does NOT render text or decide UX.
    """
    type: Literal["DELIBERATIVE_CONTINUE"]


def route_normal_execution(
    *,
    session: SessionState,
    user_input: str,
    memory_context: str,
    pacing_controller: PacingController,
    llm_executor: LLMExecutor,
    output_validator: OutputValidator,
    policy_engine: PolicyEngine,
    orchestrator_context: OrchestratorContext,
):
    """
    NORMAL execution route.

    Responsibilities:
    - Prepare LLM call using pacing + policy
    - Execute LLM via executor
    - Enforce pacing decision
    - Validate output
    - Mutate session state ONLY where explicitly allowed
    """

    # 1️⃣ Fetch pacing limits (single source of truth)
    limits = pacing_controller.get_limits(session.mode)

    # 2️⃣ Build instruction block from pacing controller
    instruction = pacing_controller.build_mode_instruction(session.mode)

    # 3️⃣ Build context block (pure composition, no logic)
    context_block = f"""
SYSTEM RULES:
- Every factual claim must be labeled [HIGH], [MEDIUM], or [LOW]
- Forbidden patterns:
{policy_engine.format_forbidden_patterns()}

TURN:
{session.turn_index}
MODE:
{session.mode}

MEMORY CONTEXT:
{memory_context}

USER INPUT:
{user_input}
""".strip()

    # 4️⃣ Execute LLM (executor owns provider interaction)
    llm_result = llm_executor.execute(
        instruction=instruction,
        user_input=user_input,
        context_block=context_block,
        token_limit=limits.hard_cap_tokens,
        mode=session.mode,
        forbidden_patterns=policy_engine.get_forbidden_patterns(),
        turn_index=session.turn_index,
    )

    # 5️⃣ Evaluate pacing (pacing controller is authoritative)
    pacing_decision = pacing_controller.evaluate_output(
        session.mode,
        llm_result.token_count,
    )

    # 6️⃣ Update deliberative turn count (ONLY based on pacing decision)
    if session.mode == PacingMode.DELIBERATIVE:
        if pacing_decision.must_continue:
            session.deliberative_turn_count += 1
        else:
            session.deliberative_turn_count = 0

    # 7️⃣ Validate output (hard gate)
    validation = output_validator.validate(
        llm_result.text,
        orchestrator_context,
    )

    if validation.status == "REJECTED":
        return validation

    # 8️⃣ Deliberative continuation signal (structured, non-presentational)
    if pacing_decision.must_continue:
        return DeliberativeContinue(type="DELIBERATIVE_CONTINUE")

    # 9️⃣ Final successful output (raw text only)
    return llm_result.text