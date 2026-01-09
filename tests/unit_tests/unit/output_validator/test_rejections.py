import pytest

from output_validator.validator import OutputValidator
from output_validator.models import ErrorCode
from orchestrator.models import OrchestratorContext
from uncertainty_engine.enums import UncertaintyLevel
from policy_engine.policy_engine import PolicyEngine


# ---------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def policy_engine():
    return PolicyEngine("policy_v1.3.2.yaml")


@pytest.fixture
def validator(policy_engine):
    return OutputValidator(policy_engine)


def base_context(**overrides) -> OrchestratorContext:
    """
    Produces a valid baseline context.
    Individual tests override only what they need.
    """
    defaults = dict(
        uncertainty_level=UncertaintyLevel.LEVEL_1_2,
        memory_write_attempted=False,
        memory_confirmation_asked=False,
        memory_scope=None,
        token_count=100,
        token_limit=1000,
        user_intent="learn python error handling",
        assumptions_required=False,
        contains_medium_or_low_confidence_claims=False,
    )
    defaults.update(overrides)
    return OrchestratorContext(**defaults)


# ---------------------------------------------------------------------
# 1️⃣ TOKEN LIMIT — MUST FAIL FIRST
# ---------------------------------------------------------------------

def test_rejects_token_cap_reached(validator):
    context = base_context(token_count=1500, token_limit=1000)

    result = validator.validate("Any text", context)

    assert result.status == "REJECTED"
    assert result.error_code == ErrorCode.tokencapreached


# ---------------------------------------------------------------------
# 2️⃣ MISSING CONFIDENCE LABEL
# ---------------------------------------------------------------------

def test_rejects_missing_confidence_label(validator):
    text = "This will definitely work."

    result = validator.validate(text, base_context())

    assert result.error_code == ErrorCode.missingconfidencelabel


# ---------------------------------------------------------------------
# 3️⃣ LOW CONFIDENCE MISUSE (ASSERTIVE)
# ---------------------------------------------------------------------

def test_rejects_low_confidence_asserted(validator):
    text = "[LOW] This will definitely work."

    result = validator.validate(text, base_context())

    assert result.error_code == ErrorCode.lowconfidenceasserted


# ---------------------------------------------------------------------
# 4️⃣ UNCERTAINTY LEVEL 3 — NO CLARIFYING QUESTION
# ---------------------------------------------------------------------

def test_rejects_uncertainty_level_3_without_question(validator):
    text = "Here is the answer."

    context = base_context(
        uncertainty_level=UncertaintyLevel.LEVEL_3
    )

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.proceededwithuncertainty3


# ---------------------------------------------------------------------
# 5️⃣ UNCERTAINTY LEVEL 4–5 — NO GROUNDING QUESTIONS
# ---------------------------------------------------------------------

def test_rejects_uncertainty_level_4_without_grounding_questions(validator):
    text = "Here is my response."

    context = base_context(
        uncertainty_level=UncertaintyLevel.LEVEL_4
    )

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.proceededwithuncertainty45


# ---------------------------------------------------------------------
# 6️⃣ A/B/C RULE — PERCENTAGES
# ---------------------------------------------------------------------

def test_rejects_percentage_in_choice(validator):
    text = "Option A (70%), Option B (30%)"

    result = validator.validate(text, base_context())

    assert result.error_code == ErrorCode.percentageinchoice


# ---------------------------------------------------------------------
# 7️⃣ ASSUMPTIONS REQUIRED BUT NOT SURFACED
# ---------------------------------------------------------------------

def test_rejects_missing_assumptions_block(validator):
    text = "Here is my recommendation."

    context = base_context(assumptions_required=True)

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.assumptionsnotsurfaced


# ---------------------------------------------------------------------
# 8️⃣ FORBIDDEN AUTHORITY LANGUAGE
# ---------------------------------------------------------------------

def test_rejects_authoritative_language(validator):
    text = "You must do this."

    result = validator.validate(text, base_context())

    assert result.error_code == ErrorCode.forbiddenauthoritativephrasing


# ---------------------------------------------------------------------
# 9️⃣ MEMORY WRITE WITHOUT CONFIRMATION
# ---------------------------------------------------------------------

def test_rejects_memory_write_without_confirmation(validator):
    text = "I will remember this."

    context = base_context(
        memory_write_attempted=True,
        memory_confirmation_asked=False
    )

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.memorywritewithoutconfirmation


def test_rejects_memory_write_without_scope(validator):
    text = "I will remember this."

    context = base_context(
        memory_write_attempted=True,
        memory_confirmation_asked=True,
        memory_scope=None
    )

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.memorywithoutscope


# ---------------------------------------------------------------------
# 🔟 INTENT NOT ADDRESSED
# ---------------------------------------------------------------------

def test_rejects_intent_not_addressed(validator):
    text = "Here is unrelated content."

    context = base_context(user_intent="python decorators")

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.intentnotaddressed


# ---------------------------------------------------------------------
# 1️⃣1️⃣ UNCERTAINTY NOT DISCLOSED
# ---------------------------------------------------------------------

def test_rejects_missing_uncertainty_language(validator):
    text = "This is the correct answer."

    context = base_context(
        contains_medium_or_low_confidence_claims=True
    )

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.uncertaintynotdisclosed


# ---------------------------------------------------------------------
# 1️⃣2️⃣ NEXT STEPS NOT CLEAR
# ---------------------------------------------------------------------

def test_rejects_missing_next_steps(validator):
    text = "Here is the explanation."

    result = validator.validate(text, base_context())

    assert result.error_code == ErrorCode.nextstepsnotclear


# ---------------------------------------------------------------------
# 🆕 1️⃣3️⃣ INVALID A/B/C FORMAT (NO OPTIONS)
# ---------------------------------------------------------------------

def test_rejects_invalid_user_choice_format(validator):
    text = "Choose wisely."

    result = validator.validate(text, base_context())

    assert result.error_code == ErrorCode.invaliduserchoiceformat


# ---------------------------------------------------------------------
# 🆕 1️⃣4️⃣ MULTIPLE GROUNDED QUESTIONS REQUIRED BUT ONLY ONE PRESENT
# ---------------------------------------------------------------------

def test_rejects_insufficient_grounding_questions_level_5(validator):
    text = "Can you clarify?"

    context = base_context(
        uncertainty_level=UncertaintyLevel.LEVEL_5
    )

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.proceededwithuncertainty45


# ---------------------------------------------------------------------
# 🆕 1️⃣5️⃣ LOW CONFIDENCE ASSERTED WITH COMMAND LANGUAGE
# ---------------------------------------------------------------------

def test_rejects_low_confidence_with_imperative(validator):
    text = "[LOW] You should definitely do this."

    result = validator.validate(text, base_context())

    assert result.error_code == ErrorCode.lowconfidenceasserted


# ---------------------------------------------------------------------
# FAIL-FAST ORDER VERIFICATION
# Token cap must win over all other violations
# ---------------------------------------------------------------------

def test_fail_fast_token_cap_preempts_all_other_rules(validator):
    text = "[LOW] You must do this."

    context = base_context(
        token_count=5000,
        token_limit=100,
        uncertainty_level=UncertaintyLevel.LEVEL_5,
        memory_write_attempted=True,
        assumptions_required=True,
        contains_medium_or_low_confidence_claims=True,
    )

    result = validator.validate(text, context)

    assert result.error_code == ErrorCode.tokencapreached