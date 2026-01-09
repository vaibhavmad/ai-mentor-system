import pytest

from output_validator.validator import OutputValidator
from output_validator.models import ErrorCode
from orchestrator.models import OrchestratorContext
from uncertainty_engine.enums import UncertaintyLevel
from policy_engine.policy_engine import PolicyEngine


@pytest.fixture
def validator():
    policy = PolicyEngine("policy_v1.3.2.yaml")
    return OutputValidator(policy)


# ---------------------------------------------------------
# EDGE CASE 1: Token limit exactly equal (should PASS)
# ---------------------------------------------------------
def test_token_count_equal_to_limit_is_allowed(validator):
    text = "[HIGH] This is valid.\nNext steps: proceed."
    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_1_2,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=100,
        token_limit=100,
        user_intent="explain",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )

    result = validator.validate(text, context)
    assert result.status == "ACCEPTED"


# ---------------------------------------------------------
# EDGE CASE 2: Multiple violations — first rule must win
# Token overflow + missing confidence label
# ---------------------------------------------------------
def test_fail_fast_order_token_rule_wins(validator):
    text = "This is an answer without confidence label."
    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_1_2,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=200,
        token_limit=100,  # token violation FIRST
        user_intent="answer",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )

    result = validator.validate(text, context)
    assert result.status == "REJECTED"
    assert result.error_code == ErrorCode.tokencapreached


# ---------------------------------------------------------
# EDGE CASE 3: LOW confidence but properly hedged (PASS)
# ---------------------------------------------------------
def test_low_confidence_with_uncertainty_language_allowed(validator):
    text = (
        "[LOW] This might work depending on context.\n"
        "I am not sure, but possibly.\n"
        "Next steps: clarify constraints."
    )

    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_1_2,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=50,
        token_limit=200,
        user_intent="advice",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=True,
    )

    result = validator.validate(text, context)
    assert result.status == "ACCEPTED"


# ---------------------------------------------------------
# EDGE CASE 4: LEVEL 4 uncertainty with exactly 3 questions
# ---------------------------------------------------------
def test_level4_exactly_three_grounding_questions_allowed(validator):
    text = (
        "[HIGH] I need more information.\n"
        "What is your goal?\n"
        "What constraints apply?\n"
        "What timeline are you on?\n"
        "Next steps: answer these questions."
    )

    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_4,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=80,
        token_limit=200,
        user_intent="plan",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )

    result = validator.validate(text, context)
    assert result.status == "ACCEPTED"


# ---------------------------------------------------------
# EDGE CASE 5: Intent barely addressed (1 keyword hit)
# ---------------------------------------------------------
def test_intent_addressed_with_single_keyword_hit(validator):
    text = (
        "[HIGH] This response explains the architecture.\n"
        "Next steps: review components."
    )

    context = OrchestratorContext(
        uncertainty_level=UncertaintyLevel.LEVEL_1_2,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=60,
        token_limit=200,
        user_intent="architecture design",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )

    result = validator.validate(text, context)
    assert result.status == "ACCEPTED"