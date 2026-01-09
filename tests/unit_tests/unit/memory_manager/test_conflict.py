from datetime import datetime

from memory_manager.conflict import is_conflict
from memory_manager.enums import DecayStatus
from memory_manager.models import MemoryEntry


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def now():
    return datetime.utcnow()


def make_entry(
    *,
    id: str,
    context: str,
    content: str,
):
    return MemoryEntry(
        id=id,
        context=context,
        content=content,
        confidence_level="HIGH",
        source="user_confirmed",
        promotion_gate=3,
        created_at=now(),
        last_used_at=now(),
        status=DecayStatus.ACTIVE,
    )


# --------------------------------------------------
# TESTS
# --------------------------------------------------

def test_direct_contradiction_detected():
    a = make_entry(
        id="a",
        context="learning",
        content="User prefers async feedback",
    )
    b = make_entry(
        id="b",
        context="learning",
        content="User prefers sync feedback",
    )

    assert is_conflict(a, b) is True


def test_negation_detected():
    a = make_entry(
        id="a",
        context="learning",
        content="User does not like deadlines",
    )
    b = make_entry(
        id="b",
        context="learning",
        content="User likes strict deadlines",
    )

    assert is_conflict(a, b) is True


def test_same_content_not_conflict():
    a = make_entry(
        id="a",
        context="learning",
        content="User prefers visual examples",
    )
    b = make_entry(
        id="b",
        context="learning",
        content="User prefers visual examples",
    )

    assert is_conflict(a, b) is False


def test_different_context_not_conflict():
    a = make_entry(
        id="a",
        context="learning",
        content="User prefers async feedback",
    )
    b = make_entry(
        id="b",
        context="planning",
        content="User prefers async feedback",
    )

    # 🔒 HARD RULE: context mismatch blocks conflict detection
    assert is_conflict(a, b) is False