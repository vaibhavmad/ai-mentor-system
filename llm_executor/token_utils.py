"""
Token counting utilities.

IMPORTANT:
- This module is for diagnostics and testing ONLY.
- It MUST NOT be used for enforcement.
- Provider-reported usage is always the source of truth at runtime.
"""

try:
    import tiktoken

    _ENCODER = tiktoken.get_encoding("cl100k_base")

    def estimate_tokens(text: str) -> int:
        """
        Preferred token estimator using tiktoken.

        Deterministic and aligned with OpenAI tokenization.
        """
        if not text:
            return 0
        return len(_ENCODER.encode(text))

except Exception:
    def estimate_tokens(text: str) -> int:
        """
        Conservative fallback estimator.

        Rules:
        - Never underestimates badly
        - Deterministic
        - Used ONLY if tiktoken is unavailable
        """
        if not text:
            return 0
        return max(1, len(text) // 4 + 1)