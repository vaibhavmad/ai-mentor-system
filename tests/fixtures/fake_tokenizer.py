class FakeTokenizer:
    """
    Deterministic tokenizer replacement.
    """

    def count(self, text: str) -> int:
        return max(1, len(text) // 4)