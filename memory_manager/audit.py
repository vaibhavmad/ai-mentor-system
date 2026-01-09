import sqlite3
from datetime import datetime
from uuid import uuid4

from memory_manager.storage import get_connection


# --------------------------------------------------
# Internal helper
# --------------------------------------------------

def _write_audit_event(
    event_type: str,
    memory_id: str | None = None,
    details: str | None = None,
) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memory_audit_log (
            id,
            timestamp,
            event_type,
            memory_id,
            details
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            datetime.utcnow().isoformat(),
            event_type,
            memory_id,
            details,
        ),
    )

    conn.commit()
    conn.close()


# --------------------------------------------------
# Canonical audit events (FINAL SPEC)
# --------------------------------------------------

def audit_memory_created(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_created",
        memory_id=memory_id,
    )


def audit_memory_proposed(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_proposed",
        memory_id=memory_id,
    )


def audit_memory_confirmed(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_confirmed",
        memory_id=memory_id,
    )


def audit_memory_rejected(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_rejected",
        memory_id=memory_id,
    )


def audit_memory_conflict_detected(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_conflict_detected",
        memory_id=memory_id,
    )


def audit_memory_conflict_resolved(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_conflict_resolved",
        memory_id=memory_id,
    )


def audit_memory_marked_stale(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_marked_stale",
        memory_id=memory_id,
    )


def audit_memory_reconfirmed(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_reconfirmed",
        memory_id=memory_id,
    )


def audit_memory_marked_historical(memory_id: str) -> None:
    _write_audit_event(
        event_type="memory_marked_historical",
        memory_id=memory_id,
    )