import pytest
from policy_engine.policy_engine import PolicyEngine
from policy_engine.errors import PolicyValidationError


def test_policy_engine_success(tmp_path):
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text("""
version: "1.3.2"
status: execution-sealed
contract: binding
driftforbidden: true
non_negotiable_rules: []
claim_confidence:
  forbidden: []
memory:
  requiredparametersbycontext:
    learning: []
  decay:
    days: 1
  promotion:
    gate1: ""
    gate2: ""
    gate3: ""
  conflict_resolution:
    behavior: []
uncertainty:
  binarychecks: [a, b, c]
  mapping:
    allyes: X
    oneno: Y
    twoormoreno: Z
groundingprotocol:
  numquestions: 1
  questions:
    learning:
      - "Q1"
  sixthquestionrule:
    decision_logic: ""
    examples: []
pacing:
  modes: {}
llmexecutor: {}
outputvalidation: {}
error_messages:
  dummy: msg
bootvalidation:
  required_sections: []
""")

    engine = PolicyEngine(str(policy_file))
    assert engine is not None


def test_policy_engine_invalid_policy(tmp_path):
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text("version: wrong")

    with pytest.raises(PolicyValidationError):
        PolicyEngine(str(policy_file))