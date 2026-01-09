class TokenLimitExceededError(Exception):
    """
    Raised when the generated output exceeds the hard token cap.

    This is a NON-RECOVERABLE error.
    The output must be rejected immediately.
    No retries, truncation, or continuation are allowed.
    """
    pass