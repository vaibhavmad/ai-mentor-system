import pytest

from pacing_controller.controller import PacingController
from pacing_controller.enums import PacingMode
from policy_engine.policy_engine import PolicyEngine


@pytest.fixture
def pacing_controller():
    policy_engine = PolicyEngine("policy_v1.3.2.yaml")
    return PacingController(policy_engine)


# ---------------------------------------------------------------------
# PREPARE REQUEST — BASIC CONTRACT
# ---------------------------------------------------------------------

def test_prepare_request_returns_required_fields(pacing_controller):
    """
    prepare_request must return:
    - max_tokens
    - instruction_prefix
    """

    result = pacing_controller.prepare_request(
        mode=PacingMode.NORMAL,
        user_choice=None,
    )

    assert isinstance(result, dict)
    assert "max_tokens" in result
    assert "instruction_prefix" in result
    assert isinstance(result["max_tokens"], int)
    assert isinstance(result["instruction_prefix"], str)


def test_prepare_request_max_tokens_equals_hard_cap(pacing_controller):
    """
    max_tokens passed to the LLM must equal the hard cap,
    never the target.
    """

    limits = pacing_controller.get_limits(PacingMode.NORMAL)

    result = pacing_controller.prepare_request(
        mode=PacingMode.NORMAL,
        user_choice=None,
    )

    assert result["max_tokens"] == limits.hard_cap_tokens


# ---------------------------------------------------------------------
# MODE-SPECIFIC BEHAVIOR (CAPABILITY-BASED, NOT STRING-COUPLED)
# ---------------------------------------------------------------------

def test_normal_mode_is_single_turn(pacing_controller):
    """
    NORMAL mode must be single-turn (no multi-turn capability).
    """

    limits = pacing_controller.get_limits(PacingMode.NORMAL)

    assert limits.multiturn is False


def test_careful_mode_is_single_turn(pacing_controller):
    """
    CAREFUL mode must be single-turn (no multi-turn capability).
    """

    limits = pacing_controller.get_limits(PacingMode.CAREFUL)

    assert limits.multiturn is False


def test_deliberative_mode_is_multiturn(pacing_controller):
    """
    DELIBERATIVE mode must explicitly support multi-turn behavior.
    """

    limits = pacing_controller.get_limits(PacingMode.DELIBERATIVE)

    assert limits.multiturn is True


# ---------------------------------------------------------------------
# INVALID INPUT — FAIL FAST
# ---------------------------------------------------------------------

def test_prepare_request_invalid_mode_fails(pacing_controller):
    """
    prepare_request must fail if mode is invalid.
    """

    class FakeMode:
        value = "fake"

    with pytest.raises(Exception):
        pacing_controller.prepare_request(
            mode=FakeMode(),
            user_choice=None,
        )