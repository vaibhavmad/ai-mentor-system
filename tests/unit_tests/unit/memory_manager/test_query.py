from datetime import datetime

from memory_manager.manager import query_memory
from memory_manager.enums import MemoryQueryResult, DecayStatus
from memory_manager.models import MemoryEntry
from memory_manager.storage import get_connection


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def now():
    return datetime.utcnow()


def clear_memory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memory_entries")
    conn.commit()
    conn.close()


def insert_entry(entry: MemoryEntry):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO memory_entries (
            id, context, content, confidence_level, source,
            promotion_gate, created_at, last_used_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.id,
            entry.context,
            entry.content,
            entry.confidence_level,
            entry.source,
            entry.promotion_gate,
            entry.created_at.isoformat(),
            entry.last_used_at.isoformat(),
            entry.status.value,
        ),
    )
    conn.commit()
    conn.close()


def make_entry(id: str, content: str):
    return MemoryEntry(
        id=id,
        context="learning",
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

def test_query_empty():
    clear_memory()

    state, entries = query_memory("learning")

    assert state == MemoryQueryResult.EMPTY
    assert len(entries) == 0


def test_query_present_single_entry():
    clear_memory()

    entry = make_entry("m1", "Prefers visual examples")
    insert_entry(entry)

    state, entries = query_memory("learning")

    assert state == MemoryQueryResult.PRESENT
    assert len(entries) == 1
    assert entries[0].content == entry.content


def test_query_partial_multiple_non_conflicting():
    clear_memory()

    insert_entry(make_entry("m1", "Prefers visual examples"))
    insert_entry(make_entry("m2", "Likes step by step explanations"))

    state, entries = query_memory("learning")

    assert state == MemoryQueryResult.PARTIAL
    assert len(entries) == 2

    # Ensure no mutation
    contents = {e.content for e in entries}
    assert contents == {
        "Prefers visual examples",
        "Likes step by step explanations",
    }


def test_query_conflict_detected():
    clear_memory()

    insert_entry(make_entry("m1", "Prefers async feedback"))
    insert_entry(make_entry("m2", "Prefers sync feedback"))

    state, entries = query_memory("learning")

    assert state == MemoryQueryResult.CONFLICT
    assert len(entries) == 2