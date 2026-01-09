from policy_engine.validator import validate_policy


def test_validator_idempotent():
    policy = {
        "version": "1.3.2",
        "status": "execution-sealed",
        "contract": "binding",
        "driftforbidden": True,
        "non_negotiable_rules": [],
        "claim_confidence": {"forbidden": []},
        "memory": {
            "requiredparametersbycontext": {
                "learning": []
            },
            "decay": {"days": 1},
            "promotion": {"gate1": "", "gate2": "", "gate3": ""},
            "conflict_resolution": {"behavior": []},
        },
        "uncertainty": {
            "binarychecks": ["a", "b", "c"],
            "mapping": {"allyes": "X", "oneno": "Y", "twoormoreno": "Z"},
        },
        "groundingprotocol": {
            "numquestions": 1,
            "questions": {
                "learning": ["Q1"]
            },
            "sixthquestionrule": {"decision_logic": "", "examples": []},
        },
        "pacing": {"modes": {}},
        "llmexecutor": {},
        "outputvalidation": {},
        "error_messages": {"dummy": "msg"},
        "bootvalidation": {"required_sections": []},
    }

    validate_policy(policy)
    validate_policy(policy)

    # policy must remain unchanged
    assert policy["version"] == "1.3.2"