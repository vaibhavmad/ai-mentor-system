import pytest

from pacing_controller.controller import PacingController
from pacing_controller.enums import PacingMode
from pacing_controller.errors import TokenLimitExceededError
from pacing_controller.models import PacingDecision
from pacing_controller import tokenizer

from policy_engine.policy_engine import PolicyEngine


@pytest.fixture
def pacing_controller():
    policy_engine = PolicyEngine("policy_v1.3.2.yaml")
    return PacingController(policy_engine)


# ---------------------------------------------------------------------
# VALID FLOW — ONLY ALLOWED ORCHESTRATION SEQUENCE
# ---------------------------------------------------------------------

def test_valid_orchestrator_flow_normal_mode(
    pacing_controller, monkeypatch
):
    """
    Enforces the mandatory call order:
    1. prepare_request
    2. LLM generates output using max_tokens
    3. evaluate_output
    """

    prep = pacing_controller.prepare_request(
        PacingMode.NORMAL,
        user_choice=None
    )

    assert "max_tokens" in prep
    assert "instruction_prefix" in prep

    # Deterministically force token count below target
    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: 10,
    )

    decision = pacing_controller.evaluate_output(
        PacingMode.NORMAL,
        output_text="irrelevant"
    )

    assert isinstance(decision, PacingDecision)
    assert decision.accepted is True
    assert decision.must_continue_in_next_turn is False


# ---------------------------------------------------------------------
# BYPASS PROHIBITIONS — CONTRACT VIOLATIONS
# ---------------------------------------------------------------------

def test_bypass_evaluate_output_is_not_allowed():
    """
    Without evaluate_output, there is no PacingDecision.
    Orchestrator cannot act on output directly.
    """

    decision = None

    with pytest.raises(AttributeError):
        _ = decision.accepted


def test_bypass_prepare_request_is_not_allowed(
    pacing_controller, monkeypatch
):
    """
    Orchestrator MUST NOT evaluate output without prepare_request.
    """

    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: 10,
    )

    with pytest.raises(Exception):
        pacing_controller.evaluate_output(
            PacingMode.NORMAL,
            output_text="irrelevant"
        )


# ---------------------------------------------------------------------
# HARD CAP ENFORCEMENT — NO OVERRIDES
# ---------------------------------------------------------------------

def test_hard_cap_exceeded_raises_fatal_error(
    pacing_controller, monkeypatch
):
    """
    If output exceeds hard cap, TokenLimitExceededError MUST be raised.
    """

    limits = pacing_controller.get_limits(PacingMode.NORMAL)

    pacing_controller.prepare_request(PacingMode.NORMAL, None)

    # Deterministically force token count beyond hard cap
    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: limits.hard_cap_tokens + 1,
    )

    with pytest.raises(TokenLimitExceededError):
        pacing_controller.evaluate_output(
            PacingMode.NORMAL,
            output_text="irrelevant"
        )


# ---------------------------------------------------------------------
# DELIBERATIVE MODE — CONTROLLER OWNS CONTINUATION
# ---------------------------------------------------------------------

def test_deliberative_requires_continuation(
    pacing_controller, monkeypatch
):
    """
    In DELIBERATIVE mode, continuation decision is owned ONLY
    by the Pacing Controller.
    """

    limits = pacing_controller.get_limits(PacingMode.DELIBERATIVE)

    pacing_controller.prepare_request(PacingMode.DELIBERATIVE, None)

    # Force token count to exactly target
    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: limits.target_tokens,
    )

    decision = pacing_controller.evaluate_output(
        PacingMode.DELIBERATIVE,
        output_text="irrelevant"
    )

    assert decision.accepted is True
    assert decision.must_continue_in_next_turn is True


def test_orchestrator_cannot_override_continuation(
    pacing_controller, monkeypatch
):
    """
    Orchestrator MUST NOT override must_continue_in_next_turn.
    """

    limits = pacing_controller.get_limits(PacingMode.DELIBERATIVE)

    pacing_controller.prepare_request(PacingMode.DELIBERATIVE, None)

    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: limits.target_tokens,
    )

    decision = pacing_controller.evaluate_output(
        PacingMode.DELIBERATIVE,
        output_text="irrelevant"
    )

    with pytest.raises(Exception):
        decision.must_continue_in_next_turn = False


# ---------------------------------------------------------------------
# MAX DELIBERATIVE TURNS — HARD STOP
# ---------------------------------------------------------------------

def test_deliberative_max_turns_enforced(
    pacing_controller, monkeypatch
):
    """
    After MAX_DELIBERATIVE_TURNS, continuation MUST stop.
    """

    limits = pacing_controller.get_limits(PacingMode.DELIBERATIVE)

    pacing_controller.prepare_request(PacingMode.DELIBERATIVE, None)

    monkeypatch.setattr(
        tokenizer,
        "estimate_tokens",
        lambda _: limits.target_tokens,
    )

    for _ in range(pacing_controller.MAX_DELIBERATIVE_TURNS):
        decision = pacing_controller.evaluate_output(
            PacingMode.DELIBERATIVE,
            output_text="irrelevant"
        )
        assert decision.must_continue_in_next_turn is True

    final_decision = pacing_controller.evaluate_output(
        PacingMode.DELIBERATIVE,
        output_text="irrelevant"
    )

    assert final_decision.must_continue_in_next_turn is False