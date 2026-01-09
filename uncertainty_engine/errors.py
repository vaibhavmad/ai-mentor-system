class UncertaintyEngineError(Exception):
    """
    Base class for all uncertainty engine fatal errors.
    """
    pass


class AmbiguousContextError(UncertaintyEngineError):
    """
    Raised when user input matches multiple contexts
    and cannot be resolved deterministically.
    """

    def __init__(self, matches):
        message = (
            "Ambiguous context detected. "
            f"Multiple contexts matched: {matches}. "
            "Unable to determine a single safe context."
        )
        super().__init__(message)
        self.matches = matches


class InvalidContextError(UncertaintyEngineError):
    """
    Raised when an invalid or unsupported context is encountered.
    """

    def __init__(self, context):
        message = f"Invalid context detected: {context}"
        super().__init__(message)
        self.context = context