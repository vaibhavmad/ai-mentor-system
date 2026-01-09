import copy
import pytest
import yaml
from policy_engine.api import PolicyAPI


def test_api_returns_copy():
    policy = {"a": {"b": 1}}
    api = PolicyAPI(policy)

    result = api.get_policy()
    assert result == policy
    assert result is not policy


def test_api_is_read_only():
    policy = {"a": {"b": 1}}
    api = PolicyAPI(policy)

    result = api.get_policy()
    result["a"]["b"] = 999

# original policy must remain unchanged
    assert policy["a"]["b"] == 1

def load_policy():
    with open("policy_v1.3.2.yaml", "r") as f:
        return yaml.safe_load(f)


def test_get_token_limits_deepcopy():
    api = PolicyAPI(load_policy())
    data = api.get_token_limits("normal")
    data["targettokens"] = 9999

    fresh = api.get_token_limits("normal")
    assert fresh["targettokens"] != 9999


def test_get_token_limits_invalid_mode():
    api = PolicyAPI(load_policy())

    with pytest.raises(KeyError):
        api.get_token_limits("invalid_mode")


def test_get_uncertainty_matrix_deepcopy():
    api = PolicyAPI(load_policy())
    data = api.get_uncertainty_matrix()
    data["binarychecks"].append("fake")

    fresh = api.get_uncertainty_matrix()
    assert "fake" not in fresh["binarychecks"]


def test_get_user_choice_template_deepcopy():
    api = PolicyAPI(load_policy())
    data = api.get_user_choice_template()
    data["options"]["A"] = "mutated"

    fresh = api.get_user_choice_template()
    assert fresh["options"]["A"] != "mutated"


def test_get_grounding_questions_deepcopy():
    api = PolicyAPI(load_policy())
    data = api.get_grounding_questions("learning")
    data.append("fake")

    fresh = api.get_grounding_questions("learning")
    assert "fake" not in fresh


def test_get_grounding_questions_invalid_context():
    api = PolicyAPI(load_policy())

    with pytest.raises(KeyError):
        api.get_grounding_questions("invalid_context")


def test_get_output_validation_rules_deepcopy():
    api = PolicyAPI(load_policy())
    data = api.get_output_validation_rules()
    data["mustcheck"].append("fake")

    fresh = api.get_output_validation_rules()
    assert "fake" not in fresh["mustcheck"]


def test_get_claim_confidence_rules_deepcopy():
    api = PolicyAPI(load_policy())
    data = api.get_claim_confidence_rules()
    data["labels"]["HIGH"] = "mutated"

    fresh = api.get_claim_confidence_rules()
    assert fresh["labels"]["HIGH"] != "mutated"


def test_get_memory_promotion_rules_deepcopy():
    api = PolicyAPI(load_policy())
    data = api.get_memory_promotion_rules()
    data["gate1"] = "mutated"

    fresh = api.get_memory_promotion_rules()
    assert fresh["gate1"] != "mutated"


def test_get_error_message_valid_code():
    api = PolicyAPI(load_policy())
    msg = api.get_error_message("missing_confidence_label")
    assert isinstance(msg, str)


def test_get_error_message_invalid_code():
    api = PolicyAPI(load_policy())

    with pytest.raises(KeyError):
        api.get_error_message("invalid_error_code")