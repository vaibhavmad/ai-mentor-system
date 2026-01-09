from uncertainty_engine.enums import BinaryCheck


VAGUE_PHRASES = [
    "make it better",
    "improve this",
    "help me",
    "what should i do",
    "do something",
    "fix this",
]


def check_intent(text: str) -> BinaryCheck:
    text_lower = text.lower()

    for phrase in VAGUE_PHRASES:
        if phrase in text_lower:
            return BinaryCheck.NO

    return BinaryCheck.YES