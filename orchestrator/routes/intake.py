from orchestrator.models import IntakeResponse
from policy_engine.policy_engine import PolicyEngine


def route_intake(policy_engine: PolicyEngine) -> IntakeResponse:
    """
    INTAKE route.

    Responsibilities:
    - Fetch intake questions from PolicyEngine
    - Return structured IntakeResponse only

    Non-responsibilities:
    - No prose rendering
    - No UI formatting
    - No routing decisions
    - No state mutation
    """

    questions = policy_engine.get_intake_questions()

    return IntakeResponse(
        type="INTAKE",
        questions=questions,
    )