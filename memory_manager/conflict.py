from typing import Tuple, List

from memory_manager.models import MemoryEntry


NEGATION_PAIRS = [
    ("prefer", "avoid"),
    ("use", "not use"),
    ("likes", "dislikes"),
    ("async", "sync"),
    ("remote", "onsite"),
    ("yes", "no"),
]


def normalize(text: str) -> str:
    return text.lower().strip()


def semantic_contradiction(a: str, b: str) -> bool:
    """
    Deterministic, rule-based contradiction detection.
    """

    a_norm = normalize(a)
    b_norm = normalize(b)

    # Direct negation
    if a_norm == f"not {b_norm}" or b_norm == f"not {a_norm}":
        return True

    # Known opposite pairs
    for x, y in NEGATION_PAIRS:
        if x in a_norm and y in b_norm:
            return True
        if y in a_norm and x in b_norm:
            return True

    return False


def is_conflict(e1: MemoryEntry, e2: MemoryEntry) -> bool:
    """
    Conflict exists only if:
    - same context
    - semantic contradiction in content
    """
    if e1.context != e2.context:
        return False

    return semantic_contradiction(e1.content, e2.content)


# Resolution constants (unchanged)
RESOLUTION_CHOOSE_A = "A"
RESOLUTION_CHOOSE_B = "B"
RESOLUTION_BOTH_TRUE = "BOTH"
RESOLUTION_UNSURE = "UNSURE"


def resolve_conflict(
    choice: str,
    entry_a: MemoryEntry,
    entry_b: MemoryEntry,
) -> Tuple[List[MemoryEntry], bool]:
    """
    Resolve conflict strictly based on user choice.
    """

    if choice == RESOLUTION_CHOOSE_A:
        return [entry_a], True

    if choice == RESOLUTION_CHOOSE_B:
        return [entry_b], True

    if choice == RESOLUTION_BOTH_TRUE:
        return [entry_a, entry_b], True

    if choice == RESOLUTION_UNSURE:
        return [entry_a, entry_b], False

    raise ValueError(f"Invalid conflict resolution choice: {choice}")