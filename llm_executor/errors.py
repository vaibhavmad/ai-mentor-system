class LLMExecutionError(Exception):
    """
    Raised for INTERNAL executor failures.

    This includes:
    - Invalid or malformed LLMRequest
    - Prompt construction failures
    - Adapter misconfiguration
    - Broken internal invariants

    These are programmer / system errors, not provider faults.
    """
    pass


class ProviderError(Exception):
    """
    Raised for EXTERNAL provider failures.

    This includes:
    - Network errors
    - Timeouts
    - 4xx / 5xx responses
    - Missing or malformed provider fields (e.g., missing usage)

    These indicate the LLM provider failed to fulfill a valid request.
    """
    pass