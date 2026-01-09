import pytest

from output_validator.validator import OutputValidator
from output_validator.models import ValidationResult
from orchestrator.models import OrchestratorContext
from uncertainty_engine.enums import UncertaintyLevel
from policy_engine.policy_engine import PolicyEngine


@pytest.fixture
def validator():
    policy_engine = PolicyEngine("policy_v1.3.2.yaml")
    return OutputValidator(policy_engine)


# ---------------------------------------------------------------------
# ACCEPTANCE CASES — MUST PASS WITHOUT REJECTION
# ---------------------------------------------------------------------

def test_accepts_clear_response_normal_uncertainty(validator):
    """
    Fully compliant response under LEVEL 1–2 uncertainty.
    """
    text = (
        "[HIGH] This approach works because it follows standard principles.\n\n"
        "Next steps:\n"
        "You can now apply this method to your use case."
    )

    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_1_2,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=200,
        token_limit=1000,
        user_intent="understand approach",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )

    result = validator.validate(text, context)

    assert result.status == "ACCEPTED"
    assert result.error_code is None
    assert result.message is None


def test_accepts_level_3_with_clarifying_question(validator):
    """
    LEVEL 3 must ask a clarifying question.
    """
    text = (
        "[HIGH] This depends on your constraints.\n\n"
        "Could you clarify your primary goal?\n\n"
        "Next steps:\n"
        "Let me know once you clarify."
    )

    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_3,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=180,
        token_limit=1000,
        user_intent="decide approach",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )

    result = validator.validate(text, context)

    assert result.status == "ACCEPTED"
    assert result.error_code is None
    assert result.message is None


def test_accepts_level_4_with_grounding_questions(validator):
    """
    LEVEL 4 must include >= 3 grounding questions.
    """
    text = (
        "[HIGH] To proceed safely, I need more information.\n\n"
        "What is your timeline?\n"
        "What constraints do you have?\n"
        "What outcome are you aiming for?\n\n"
        "Next steps:\n"
        "Please answer the questions above."
    )

    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_4,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=250,
        token_limit=1000,
        user_intent="plan solution",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )

    result = validator.validate(text, context)

    assert result.status == "ACCEPTED"
    assert result.error_code is None
    assert result.message is None


def test_accepts_low_confidence_with_uncertainty_language(validator):
    """
    LOW confidence is allowed when uncertainty is disclosed properly.
    """
    text = (
        "[LOW] This might work, but I am not sure.\n\n"
        "It possibly depends on external factors.\n\n"
        "Next steps:\n"
        "Let me know if you want to explore alternatives."
    )

    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_1_2,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=160,
        token_limit=1000,
        user_intent="evaluate option",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=True,
    )

    result = validator.validate(text, context)

    assert result.status == "ACCEPTED"
    assert result.error_code is None
    assert result.message is None


def test_accepts_memory_write_with_confirmation_and_scope(validator):
    """
    Memory write is allowed only when confirmation and scope exist.
    """
    text = (
        "[HIGH] I can remember this preference.\n\n"
        "Next steps:\n"
        "Let me know if you'd like me to store this."
    )

    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_1_2,
        memory_write_attempted=True,
        memory_confirmation_asked=True,
        memory_scope="session",
        token_count=140,
        token_limit=1000,
        user_intent="store preference",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )

    result = validator.validate(text, context)

    assert result.status == "ACCEPTED"
    assert result.error_code is None
    assert result.message is None