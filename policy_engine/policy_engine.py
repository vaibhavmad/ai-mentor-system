import copy
from typing import List

from policy_engine.loader import load_policy
from policy_engine.validator import validate_policy
from pacing_controller.enums import PacingMode
from output_validator.models import ErrorCode


class PolicyEngine:
    def __init__(self, policy_path: str):
        policy = load_policy(policy_path)
        validate_policy(policy)
        self._policy = policy

    def get_error_message(self, error_code: ErrorCode) -> str:
        """Get error message for a given error code."""
        code_str = error_code.value
        if code_str not in self._policy.get("error_messages", {}):
            raise KeyError(f"Error code '{code_str}' not found in policy")
        return copy.deepcopy(self._policy["error_messages"][code_str])

    def get_forbidden_patterns(self) -> List[str]:
        """Get list of forbidden patterns from policy."""
        forbidden = self._policy.get("userchoice", {}).get("forbidden", [])
        return copy.deepcopy(forbidden)

    def get_intake_questions(self) -> List[str]:
        """Get list of intake questions from policy."""
        questions = self._policy.get("intake", {}).get("questions", [])
        # Extract text from question dicts if they're dicts, otherwise use as-is
        if questions and isinstance(questions[0], dict):
            return copy.deepcopy([q.get("text", "") for q in questions if q.get("text")])
        return copy.deepcopy(questions)

    def get_grounding_questions(self, reason: str) -> List[str]:
        """Get grounding questions for a given reason/context."""
        # The reason parameter maps to a context in the policy
        # For now, we'll try to find it in the questions dict
        questions_dict = self._policy.get("groundingprotocol", {}).get("questions", {})
        
        # Try to find the context by matching reason or use a default
        # If reason is "high_uncertainty", we might need to pick a context
        # For now, let's try to find it directly or use the first available context
        if reason in questions_dict:
            return copy.deepcopy(questions_dict[reason])
        
        # If not found, try common context names
        for context in ["learning", "codereview", "architecturedesign", "problemsolving", 
                        "decisionmaking", "planning", "evaluation"]:
            if context in questions_dict:
                return copy.deepcopy(questions_dict[context])
        
        raise KeyError(f"Grounding questions not found for reason: {reason}")

    def recommend_mode(self, uncertainty_level: str) -> PacingMode:
        """Recommend pacing mode based on uncertainty level."""
        if uncertainty_level == "LEVEL_1":
            return PacingMode.NORMAL
        elif uncertainty_level == "LEVEL_2":
            return PacingMode.CAREFUL
        elif uncertainty_level in ["LEVEL_3", "LEVEL_4", "LEVEL_5"]:
            raise ValueError(
                f"Policy does not recommend modes for uncertainty level {uncertainty_level}"
            )
        else:
            raise ValueError(f"Unknown uncertainty level: {uncertainty_level}")

    def get_pacing_limits(self, mode: str) -> dict:
        """Get pacing limits for a given mode."""
        modes = self._policy.get("pacing", {}).get("modes", {})
        if mode not in modes:
            raise KeyError(f"Pacing mode '{mode}' not found in policy")
        limits = modes[mode]
        return {
            "target_tokens": limits.get("targettokens"),
            "hard_cap_tokens": limits.get("hardcap"),
            "multiturn": limits.get("multiturn", False),
        }

    def get_user_choice_options(self) -> dict:
        """Get user choice options (A, B, C) from policy."""
        options = self._policy.get("userchoice", {}).get("options", {})
        return copy.deepcopy(options)