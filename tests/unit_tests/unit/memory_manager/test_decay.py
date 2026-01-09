from datetime import datetime, timedelta

import pytest

from memory_manager.manager import check_and_apply_decay
from memory_manager.decay import handle_reconfirmation
from memory_manager.enums import DecayStatus
from memory_manager.models import MemoryEntry
from memory_manager.errors import DecayReconfirmationRequired
from memory_manager.storage import get_connection


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def now():
    return datetime.utcnow()


def clear_audit_log():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memory_audit_log")
    conn.commit()
    conn.close()


def fetch_audit_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT event_type FROM memory_audit_log ORDER BY timestamp"
    )
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows


def make_entry(
    *,
    id="m1",
    last_used_at,
    status=DecayStatus.ACTIVE,
):
    return MemoryEntry(
        id=id,
        context="learning",
        content="Prefers visual examples",
        confidence_level="HIGH",
        source="user_confirmed",
        promotion_gate=3,
        created_at=now() - timedelta(days=200),
        last_used_at=last_used_at,
        status=status,
    )


# --------------------------------------------------
# TESTS
# --------------------------------------------------

def test_active_to_stale_raises_and_audits():
    clear_audit_log()

    entry = make_entry(
        last_used_at=now() - timedelta(days=181)
    )

    with pytest.raises(DecayReconfirmationRequired):
        check_and_apply_decay(entry)

    events = fetch_audit_events()
    assert "memory_marked_stale" in events


def test_stale_to_reconfirmed_yes():
    clear_audit_log()

    stale_entry = make_entry(
        last_used_at=now() - timedelta(days=181),
        status=DecayStatus.STALE,
    )

    updated = handle_reconfirmation(stale_entry, user_response="yes")

    assert updated.status == DecayStatus.RECONFIRMED
    assert updated.last_used_at > stale_entry.last_used_at

    events = fetch_audit_events()
    assert "memory_reconfirmed" in events


def test_stale_to_historical_no():
    clear_audit_log()

    stale_entry = make_entry(
        last_used_at=now() - timedelta(days=181),
        status=DecayStatus.STALE,
    )

    updated = handle_reconfirmation(stale_entry, user_response="no")

    assert updated.status == DecayStatus.HISTORICAL

    events = fetch_audit_events()
    assert "memory_marked_historical" in events


def test_stale_to_conflict_unsure():
    clear_audit_log()

    stale_entry = make_entry(
        last_used_at=now() - timedelta(days=181),
        status=DecayStatus.STALE,
    )

    with pytest.raises(Exception):
        handle_reconfirmation(stale_entry, user_response="unsure")

    # Ensure no silent resolution
    events = fetch_audit_events()
    assert "memory_reconfirmed" not in events
    assert "memory_marked_historical" not in events


def test_full_decay_lifecycle_end_to_end():
    clear_audit_log()

    # Step 1: Create ACTIVE memory
    entry = make_entry(
        id="lifecycle-1",
        last_used_at=now() - timedelta(days=10),
        status=DecayStatus.ACTIVE,
    )

    # Step 2: Advance time → STALE
    stale_candidate = MemoryEntry(
        **{
            **entry.__dict__,
            "last_used_at": now() - timedelta(days=181),
        }
    )

    with pytest.raises(DecayReconfirmationRequired):
        check_and_apply_decay(stale_candidate)

    events = fetch_audit_events()
    assert events[-1] == "memory_marked_stale"

    # Step 3: Reconfirm → RECONFIRMED
    reconfirmed = handle_reconfirmation(
        stale_candidate,
        user_response="yes",
    )

    assert reconfirmed.status == DecayStatus.RECONFIRMED

    events = fetch_audit_events()
    assert "memory_reconfirmed" in events

    # Step 4: Advance time again → STALE
    stale_again = MemoryEntry(
        **{
            **reconfirmed.__dict__,
            "last_used_at": now() - timedelta(days=181),
            "status": DecayStatus.ACTIVE,
        }
    )

    with pytest.raises(DecayReconfirmationRequired):
        check_and_apply_decay(stale_again)

    events = fetch_audit_events()
    assert events.count("memory_marked_stale") == 2

    # Step 5: User says “no” → HISTORICAL
    historical = handle_reconfirmation(
        stale_again,
        user_response="no",
    )

    assert historical.status == DecayStatus.HISTORICAL

    events = fetch_audit_events()
    assert "memory_marked_historical" in events

    # Step 6: Ensure no reuse once HISTORICAL
    with pytest.raises(DecayReconfirmationRequired):
        check_and_apply_decay(historical)