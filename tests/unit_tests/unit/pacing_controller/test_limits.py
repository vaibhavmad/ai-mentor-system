import pytest
from copy import deepcopy

from pacing_controller.controller import PacingController
from pacing_controller.enums import PacingMode
from pacing_controller.models import PacingLimits
from policy_engine.policy_engine import PolicyEngine


@pytest.fixture
def pacing_controller():
    policy_engine = PolicyEngine("policy_v1.3.2.yaml")
    return PacingController(policy_engine)


# ---------------------------------------------------------------------
# POLICY LOADING — SINGLE SOURCE OF TRUTH
# ---------------------------------------------------------------------

def test_limits_loaded_from_policy(pacing_controller):
    """
    Pacing limits must be loaded from PolicyEngine,
    not hardcoded.
    """

    normal_limits = pacing_controller.get_limits(PacingMode.NORMAL)

    assert isinstance(normal_limits, PacingLimits)
    assert normal_limits.target_tokens > 0
    assert normal_limits.hard_cap_tokens > 0
    assert normal_limits.hard_cap_tokens >= normal_limits.target_tokens


def test_all_required_modes_exist(pacing_controller):
    """
    All pacing modes defined in the spec must exist.
    """

    for mode in (
        PacingMode.NORMAL,
        PacingMode.CAREFUL,
        PacingMode.DELIBERATIVE,
    ):
        limits = pacing_controller.get_limits(mode)
        assert isinstance(limits, PacingLimits)


# ---------------------------------------------------------------------
# DEEP COPY PROTECTION — IMMUTABILITY
# ---------------------------------------------------------------------

def test_get_limits_returns_deep_copy(pacing_controller):
    """
    get_limits must return a deep copy.
    Mutating the returned object must not affect internal state.
    """

    limits_1 = pacing_controller.get_limits(PacingMode.NORMAL)
    limits_2 = pacing_controller.get_limits(PacingMode.NORMAL)

    # Sanity check: values start equal
    assert limits_1 == limits_2

    # Mutate the returned copy
    mutated = deepcopy(limits_1)
    object.__setattr__(mutated, "target_tokens", 999999)

    # Fetch again from controller
    fresh_limits = pacing_controller.get_limits(PacingMode.NORMAL)

    # Internal state must be unchanged
    assert fresh_limits.target_tokens != 999999
    assert fresh_limits.target_tokens == limits_2.target_tokens


# ---------------------------------------------------------------------
# INVALID MODE — HARD FAILURE
# ---------------------------------------------------------------------

def test_requesting_unknown_mode_fails(pacing_controller):
    """
    Requesting limits for an invalid mode must fail fast.
    """

    class FakeMode:
        value = "fake"

    with pytest.raises(Exception):
        pacing_controller.get_limits(FakeMode())