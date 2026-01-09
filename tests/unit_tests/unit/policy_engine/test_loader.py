import pytest
from policy_engine.loader import load_policy


def test_load_policy_success(tmp_path):
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text("key: value")

    data = load_policy(str(policy_file))
    assert data == {"key": "value"}


def test_load_policy_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_policy("non_existent_file.yaml")


def test_load_policy_invalid_yaml(tmp_path):
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text("key: [unclosed")

    with pytest.raises(ValueError):
        load_policy(str(policy_file))


def test_load_policy_not_dict(tmp_path):
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text("- item1\n- item2")

    with pytest.raises(ValueError):
        load_policy(str(policy_file))