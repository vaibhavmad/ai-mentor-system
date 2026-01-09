import pytest

from pacing_controller.controller import PacingController
from pacing_controller.enums import PacingMode
from pacing_controller.errors import TokenLimitExceededError
from pacing_controller.models import PacingDecision
from policy_engine.policy_engine import PolicyEngine


@pytest.fixture
def pacing_controller():
    policy_engine = PolicyEngine("policy_v1.3.2.yaml")
    return PacingController(policy_engine)


# ---------------------------------------------------------------------
# HARD CAP — FATAL ENFORCEMENT
# ---------------------------------------------------------------------

def test_output_exceeding_hard_cap_raises_error(pacing_controller):
    """
    Any output exceeding hard cap must raise TokenLimitExceededError.
    The test does NOT compute tokens; it relies on the controller.
    """

    pacing_controller.prepare_request(PacingMode.NORMAL, None)

    # Extremely large output — guaranteed to exceed any cap
    output = "x" * 100_000

    with pytest.raises(TokenLimitExceededError):
        pacing_controller.evaluate_output(
            PacingMode.NORMAL,
            output_text=output
        )


# ---------------------------------------------------------------------
# ACCEPTANCE — WITHIN CONTROLLER LIMITS
# ---------------------------------------------------------------------

def test_small_output_is_accepted(pacing_controller):
    """
    Small outputs must be accepted.
    """

    pacing_controller.prepare_request(PacingMode.NORMAL, None)

    output = "This is a short response."

    decision = pacing_controller.evaluate_output(
        PacingMode.NORMAL,
        output_text=output
    )

    assert isinstance(decision, PacingDecision)
    assert decision.accepted is True
    assert decision.must_continue_in_next_turn is False


# ---------------------------------------------------------------------
# MODE-SPECIFIC ENFORCEMENT
# ---------------------------------------------------------------------

def test_careful_mode_never_requests_continuation(pacing_controller):
    """
    CAREFUL mode must never request continuation,
    regardless of output size (unless hard cap is exceeded).
    """

    pacing_controller.prepare_request(PacingMode.CAREFUL, None)

    output = "x" * 5_000

    decision = pacing_controller.evaluate_output(
        PacingMode.CAREFUL,
        output_text=output
    )

    assert decision.accepted is True
    assert decision.must_continue_in_next_turn is False


# ---------------------------------------------------------------------
# INVALID INPUT — FAIL FAST
# ---------------------------------------------------------------------

def test_invalid_mode_in_evaluate_output_fails(pacing_controller):
    """
    evaluate_output must fail fast on invalid mode.
    """

    class FakeMode:
        value = "fake"

    with pytest.raises(Exception):
        pacing_controller.evaluate_output(
            FakeMode(),
            output_text="test"
        )