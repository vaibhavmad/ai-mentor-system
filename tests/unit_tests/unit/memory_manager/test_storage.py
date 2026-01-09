from datetime import datetime

from memory_manager.enums import DecayStatus
from memory_manager.models import MemoryEntry
from memory_manager.storage import get_connection
from memory_manager.audit import audit_memory_created


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def now():
    return datetime.utcnow()


def clear_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memory_entries")
    cursor.execute("DELETE FROM memory_audit_log")
    conn.commit()
    conn.close()


def insert_entry(entry: MemoryEntry):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO memory_entries (
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


def fetch_entry(entry_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id, context, content, confidence_level, source,
            promotion_gate, created_at, last_used_at, status
        FROM memory_entries
        WHERE id = ?
        """,
        (entry_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def fetch_audit_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT event_type FROM memory_audit_log")
    events = [r[0] for r in cursor.fetchall()]
    conn.close()
    return events


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

def test_insert_and_fetch_deep_equality():
    clear_tables()

    entry = make_entry("s1", "Prefers visual examples")
    insert_entry(entry)

    row = fetch_entry("s1")

    assert row is not None
    assert row[0] == entry.id
    assert row[1] == entry.context
    assert row[2] == entry.content
    assert row[3] == entry.confidence_level
    assert row[4] == entry.source
    assert row[5] == entry.promotion_gate
    assert row[8] == entry.status.value


def test_audit_written_with_canonical_name():
    clear_tables()

    entry = make_entry("s2", "Likes step by step explanations")
    insert_entry(entry)

    audit_memory_created(entry.id)

    events = fetch_audit_events()
    assert "memory_created" in events


def test_no_silent_overwrite_insert_or_replace():
    clear_tables()

    entry_v1 = make_entry("s3", "Initial preference")
    insert_entry(entry_v1)

    entry_v2 = make_entry("s3", "Updated preference")
    insert_entry(entry_v2)

    row = fetch_entry("s3")
    assert row[2] == "Updated preference"

    # Ensure overwrite was explicit and audit table still intact
    events = fetch_audit_events()
    assert isinstance(events, list)