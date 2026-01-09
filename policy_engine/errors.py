class PolicyValidationError(Exception):
    """
    Format:

    Policy validation failed at [section]:

      Expected: [what was expected]
      Found: [what was found]
      Context: [example]
    """

    def __init__(self, section: str, expected: str, found: str, context: str = ""):
        self.section = section
        self.expected = expected
        self.found = found
        self.context = context

        message = f"""
Policy validation failed at {self.section}:

  Expected: {self.expected}
  Found: {self.found}
  Context: {self.context}
"""
        super().__init__(message)