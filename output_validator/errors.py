class ValidationError(Exception):
    """
    Internal error raised when the Output Validator encounters
    an unexpected or invalid internal state.

    Notes:
    - This is NOT a user-facing error.
    - No messages are hardcoded here.
    - PolicyEngine owns all user-visible error messages.
    - This error should surface only during development or
      if invariants are violated.
    """
    pass