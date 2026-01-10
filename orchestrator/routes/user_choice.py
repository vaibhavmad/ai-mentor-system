from orchestrator.models import UserChoicePrompt
from policy_engine.policy_engine import PolicyEngine


def route_user_choice(policy_engine: PolicyEngine) -> UserChoicePrompt:
    """
    USER_CHOICE route (presentation-only).

    Responsibilities:
    - Fetch A/B/C options from PolicyEngine
    - Return structured UserChoicePrompt
    - NO state mutation
    - NO mode selection
    - NO routing decisions

    This route ONLY presents choices.
    """

    options = policy_engine.get_user_choice_options()

    # Defensive contract enforcement
    if not isinstance(options, dict):
        raise ValueError("PolicyEngine must return a dict for user choice options")

    required_keys = {"A", "B", "C"}
    if set(options.keys()) != required_keys:
        raise ValueError(
            "User choice options must contain exactly keys {'A', 'B', 'C'}"
        )

    return UserChoicePrompt(
        type="USER_CHOICE",
        options=options,
    )