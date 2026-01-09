import pytest
from policy_engine.validator import validate_policy
from policy_engine.errors import PolicyValidationError


def test_validator_missing_required_key():
    policy = {
        "version": "1.3.2",
        "status": "execution-sealed",
        # contract missing
    }

    with pytest.raises(PolicyValidationError):
        validate_policy(policy)


def test_validator_invalid_version():
    policy = {
        "version": "1.0.0",
        "status": "execution-sealed",
        "contract": "binding",
        "driftforbidden": True,
        "non_negotiable_rules": [],
        "claim_confidence": {},
        "memory": {},
        "uncertainty": {},
        "groundingprotocol": {},
        "pacing": {},
        "llmexecutor": {},
        "outputvalidation": {},
        "error_messages": {},
        "bootvalidation": {"required_sections": []},
    }

    with pytest.raises(PolicyValidationError):
        validate_policy(policy)


def test_validator_success_minimal_valid_policy():
    policy = {
        "version": "1.3.2",
        "status": "execution-sealed",
        "contract": "binding",
        "driftforbidden": True,
        "non_negotiable_rules": [],
        "claim_confidence": {"forbidden": []},
        "memory": {
            "requiredparametersbycontext": {},
            "decay": {"days": 1},
            "promotion": {"gate1": "", "gate2": "", "gate3": ""},
            "conflict_resolution": {"behavior": []},
        },
        "uncertainty": {
            "binarychecks": ["a", "b", "c"],
            "mapping": {"allyes": "X", "oneno": "Y", "twoormoreno": "Z"},
        },
        "groundingprotocol": {
            "numquestions": 0,
            "questions": {},
            "sixthquestionrule": {"decision_logic": "", "examples": []},
        },
        "pacing": {"modes": {}},
        "llmexecutor": {},
        "outputvalidation": {},
        "error_messages": {"dummy": "msg"},
        "bootvalidation": {"required_sections": []},
    }

    validate_policy(policy)  # should not raise