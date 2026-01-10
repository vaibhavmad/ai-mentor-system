from orchestrator.models import GroundingResponse
from policy_engine.policy_engine import PolicyEngine


def route_grounding(
    policy_engine: PolicyEngine,
    reason: str,
) -> GroundingResponse:
    """
    Grounding route handler.

    Responsibilities:
    - Fetch grounding questions from PolicyEngine
    - Return a structured GroundingResponse
    - NEVER render prose
    - NEVER branch on question count
    - ALWAYS return exactly 5 questions

    This function performs NO validation and NO routing decisions.
    """

    questions = policy_engine.get_grounding_questions(reason=reason)

    if len(questions) != 5:
        raise ValueError(
            "PolicyEngine grounding protocol violation: "
            "Expected exactly 5 grounding questions"
        )

    return GroundingResponse(
        type="GROUNDING",
        reason=reason,
        questions=questions,
    )