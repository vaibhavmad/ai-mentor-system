import yaml


def load_policy(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise
    except yaml.YAMLError as e:
        raise ValueError("Invalid YAML") from e

    if not isinstance(data, dict):
        raise ValueError("YAML root must be a dict")

    return data