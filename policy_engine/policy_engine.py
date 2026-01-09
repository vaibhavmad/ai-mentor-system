from policy_engine.loader import load_policy
from policy_engine.validator import validate_policy


class PolicyEngine:
    def __init__(self, policy_path: str):
        policy = load_policy(policy_path)
        validate_policy(policy)
        self._policy = policy