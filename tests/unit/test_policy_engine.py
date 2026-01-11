# tests/unit/test_policy_engine.py

import pytest

from policy_engine.policy_engine import PolicyEngine
from output_validator.models import ErrorCode
from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------

@pytest.fixture
def minimal_policy_engine():
    """
    Minimal valid policy for focused tests.
    """
    return PolicyEngine("tests/fixtures/sample_policies/policy_minimal.yaml")


@pytest.fixture
def full_policy_engine():
    """
    Full production policy.
    """
    return PolicyEngine("policy_v1.3.2.yaml")


# ---------------------------------------------------------------------
# BASIC LOADING & VALIDATION
# ---------------------------------------------------------------------

def test_policy_loads_successfully():
    """
    PolicyEngine should load a valid policy without errors.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")
    assert engine is not None


@pytest.mark.policy_violation
def test_missing_rule_policy_fails_loudly():
    """
    Missing required rules must raise an explicit error.
    """
    with pytest.raises(Exception):
        PolicyEngine("tests/fixtures/sample_policies/policy_missing_rule.yaml")


@pytest.mark.policy_violation
def test_conflicting_policy_fails_loudly():
    """
    Conflicting policy definitions must raise an explicit error.
    """
    with pytest.raises(Exception):
        PolicyEngine("tests/fixtures/sample_policies/policy_conflicting.yaml")


# ---------------------------------------------------------------------
# ERROR MESSAGE CONTRACT (CRITICAL)
# ---------------------------------------------------------------------

@pytest.mark.parametrize("error_code", list(ErrorCode))
def test_every_error_code_has_message(error_code):
    """
    Every ErrorCode must be backed by a non-empty message in policy.
    No orphan error codes allowed.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")
    message = engine.get_error_message(error_code)

    assert isinstance(message, str)
    assert message.strip() != ""


@pytest.mark.policy_violation
def test_unknown_error_code_fails():
    """
    Asking for an unknown error code must fail explicitly.
    """

    engine = PolicyEngine("policy_v1.3.2.yaml")

    class FakeErrorCode:
        def __init__(self):
            self.value = "not_real"

    with pytest.raises(Exception):
        engine.get_error_message(FakeErrorCode())


# ---------------------------------------------------------------------
# IMMUTABILITY & IDEMPOTENCY
# ---------------------------------------------------------------------

def test_policy_returns_are_immutable():
    """
    Returned policy data must not allow mutation of internal state.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")

    patterns_1 = engine.get_forbidden_patterns()
    patterns_2 = engine.get_forbidden_patterns()

    assert patterns_1 == patterns_2
    assert patterns_1 is not patterns_2

    patterns_1.append("ILLEGAL_MUTATION")

    assert "ILLEGAL_MUTATION" not in engine.get_forbidden_patterns()


def test_repeated_calls_are_idempotent():
    """
    Same inputs must always produce same outputs.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")

    msg1 = engine.get_error_message(ErrorCode.token_cap_reached)
    msg2 = engine.get_error_message(ErrorCode.token_cap_reached)

    assert msg1 == msg2


# ---------------------------------------------------------------------
# INTAKE & GROUNDING DEFINITIONS
# ---------------------------------------------------------------------

def test_intake_questions_exist_and_are_list():
    """
    Intake questions must exist and be a list of strings.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")

    questions = engine.get_intake_questions()

    assert isinstance(questions, list)
    assert len(questions) > 0
    assert all(isinstance(q, str) for q in questions)


def test_grounding_questions_exact_count():
    """
    Grounding questions must always be exactly 5.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")

    questions = engine.get_grounding_questions(reason="high_uncertainty")

    assert isinstance(questions, list)
    assert len(questions) == 5
    assert all(isinstance(q, str) for q in questions)


# ---------------------------------------------------------------------
# MODE RECOMMENDATION
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "uncertainty_level,expected_mode",
    [
        ("LEVEL_1", PacingMode.NORMAL),
        ("LEVEL_2", PacingMode.CAREFUL),
    ],
)
def test_policy_mode_recommendation_low_uncertainty(
    uncertainty_level, expected_mode
):
    """
    Policy must recommend modes ONLY for low uncertainty levels.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")

    mode = engine.recommend_mode(uncertainty_level=uncertainty_level)

    assert mode == expected_mode


@pytest.mark.policy_violation
def test_policy_does_not_recommend_for_level3_or_above():
    """
    Policy must not recommend execution modes for high uncertainty.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")

    for level in ["LEVEL_3", "LEVEL_4", "LEVEL_5"]:
        with pytest.raises(Exception):
            engine.recommend_mode(uncertainty_level=level)


# ---------------------------------------------------------------------
# FORBIDDEN PATTERNS
# ---------------------------------------------------------------------

def test_forbidden_patterns_are_non_empty_and_strings():
    """
    Forbidden patterns must be a non-empty list of strings.
    """
    engine = PolicyEngine("policy_v1.3.2.yaml")

    patterns = engine.get_forbidden_patterns()

    assert isinstance(patterns, list)
    assert len(patterns) > 0
    assert all(isinstance(p, str) for p in patterns)


# ---------------------------------------------------------------------
# POLICY ISOLATION
# ---------------------------------------------------------------------

def test_multiple_policy_instances_are_isolated():
    """
    Multiple PolicyEngine instances must not share state.
    """
    engine1 = PolicyEngine("policy_v1.3.2.yaml")
    engine2 = PolicyEngine("tests/fixtures/sample_policies/policy_minimal.yaml")

    patterns1 = engine1.get_forbidden_patterns()
    patterns2 = engine2.get_forbidden_patterns()

    assert patterns1 != patterns2