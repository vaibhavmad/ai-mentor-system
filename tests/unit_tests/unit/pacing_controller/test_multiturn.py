import pytest

from pacing_controller.controller import PacingController
from pacing_controller.enums import PacingMode
from pacing_controller.models import PacingDecision
from pacing_controller import tokenizer
from policy_engine.policy_engine import PolicyEngine


@pytest.fixture
def pacing_controller():
    policy_engine = PolicyEngine("policy_v1.3.2.yaml")
    return PacingController(policy_engine)


# ---------------------------------------------------------------------
# DELIBERATIVE MULTI-TURN — STATE MANAGEMENT (DETERMINISTIC)
# ---------------------------------------------------------------------

def test_deliberative_turn_count_increments_only_on_continuation(
    pacing_controller, monkeypatch
):
    """
    deliberative_turn_count must increment ONLY when
    must_continue_in_next_turn is True.
    """

    limits = pacing_controller.get_limits(PacingMode.DELIBERATIVE)

    # Force token count to be exactly at target (within cap)
    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: limits.target_tokens,
    )

    pacing_controller.prepare_request(PacingMode.DELIBERATIVE, None)

    decision = pacing_controller.evaluate_output(
        PacingMode.DELIBERATIVE,
        output_text="irrelevant"
    )

    assert isinstance(decision, PacingDecision)
    assert decision.must_continue_in_next_turn is True
    assert pacing_controller.deliberative_turn_count == 1


def test_deliberative_turn_count_does_not_increment_without_continuation(
    pacing_controller, monkeypatch
):
    """
    deliberative_turn_count must NOT increment when continuation
    is not required.
    """

    # Force token count to be safely below target
    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: 1,
    )

    pacing_controller.prepare_request(PacingMode.DELIBERATIVE, None)

    decision = pacing_controller.evaluate_output(
        PacingMode.DELIBERATIVE,
        output_text="irrelevant"
    )

    assert decision.must_continue_in_next_turn is False
    assert pacing_controller.deliberative_turn_count == 0


# ---------------------------------------------------------------------
# MAX DELIBERATIVE TURNS — HARD STOP
# ---------------------------------------------------------------------

def test_deliberative_stops_after_max_turns(
    pacing_controller, monkeypatch
):
    """
    After MAX_DELIBERATIVE_TURNS, continuation MUST stop.
    """

    limits = pacing_controller.get_limits(PacingMode.DELIBERATIVE)

    # Force continuation every time until max is reached
    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: limits.target_tokens,
    )

    pacing_controller.prepare_request(PacingMode.DELIBERATIVE, None)

    for i in range(pacing_controller.MAX_DELIBERATIVE_TURNS):
        decision = pacing_controller.evaluate_output(
            PacingMode.DELIBERATIVE,
            output_text="irrelevant"
        )
        assert decision.must_continue_in_next_turn is True
        assert pacing_controller.deliberative_turn_count == i + 1

    # One more evaluation must NOT request continuation
    final_decision = pacing_controller.evaluate_output(
        PacingMode.DELIBERATIVE,
        output_text="irrelevant"
    )

    assert final_decision.must_continue_in_next_turn is False
    assert pacing_controller.deliberative_turn_count == pacing_controller.MAX_DELIBERATIVE_TURNS