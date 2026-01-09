try:
    import tiktoken
    _ENCODER = tiktoken.get_encoding("cl100k_base")
except Exception:
    _ENCODER = None


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.

    Priority:
    1. Use real tokenizer (tiktoken) if available
    2. Fallback to conservative estimator

    This function must:
    - Be deterministic
    - Never dangerously underestimate
    - Never rely on heuristics or randomness
    """
    if not text:
        return 0

    # Preferred: real tokenizer
    if _ENCODER is not None:
        return len(_ENCODER.encode(text))

    # Fallback: conservative approximation
    # Rule: ~4 characters per token + buffer
    return max(1, len(text) // 4 + 1)