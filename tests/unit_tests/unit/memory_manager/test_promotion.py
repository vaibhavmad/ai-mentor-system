from datetime import datetime, timedelta

import pytest

from memory_manager.enums import PromotionDecision, DecayStatus
from memory_manager.models import MemoryEntry
from memory_manager.manager import propose_memory
from memory_manager.storage import get_connection


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def now():
    return datetime.utcnow()


def make_entry(
    id: str,
    content: str = "Prefers visual examples",
    source: str = "observed",
) -> MemoryEntry:
    return MemoryEntry(
        id=id,
        context="learning",
        content=content,
        confidence_level="LOW",
        source=source,
        promotion_gate=0,
        created_at=now(),
        last_used_at=now(),
        status=DecayStatus.ACTIVE,
    )


def fetch_all_memory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id, context, content, confidence_level, source,
            promotion_gate, created_at, last_used_at, status
        FROM memory_entries
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_all_memory_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM memory_entries")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def seed_memory(
    *,
    context="learning",
    content="Prefers visual examples",
    source="observed",
    promotion_gate=1,
):
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
            f"seed-{promotion_gate}",
            context,
            content,
            "HIGH",
            source,
            promotion_gate,
            now().isoformat(),
            now().isoformat(),
            DecayStatus.ACTIVE.value,
        ),
    )
    conn.commit()
    conn.close()


# --------------------------------------------------
# TESTS
# --------------------------------------------------

def test_gate_1_observe_persists_memory():
    entry = make_entry("m1")

    result = propose_memory(entry)

    assert result.promotion_decision == PromotionDecision.GATE_1_OBSERVE
    assert result.requires_user_confirmation is False

    rows = fetch_all_memory()
    assert len(rows) == 1
    assert rows[0][5] == 1  # promotion_gate
    assert rows[0][4] == "observed"  # source


def test_gate_2_flag_persists_memory():
    seed_memory(promotion_gate=1)

    entry = make_entry("m2")

    result = propose_memory(entry)

    assert result.promotion_decision == PromotionDecision.GATE_2_FLAG
    assert result.requires_user_confirmation is False

    rows = fetch_all_memory()
    assert len(rows) == 2
    assert rows[-1][5] == 2  # promotion_gate


def test_gate_3_requires_confirmation_and_does_not_persist():
    seed_memory(promotion_gate=1)
    seed_memory(promotion_gate=2)

    entry = make_entry("m3")

    result = propose_memory(entry)

    assert result.promotion_decision == PromotionDecision.GATE_3_REQUIRE_CONFIRMATION
    assert result.requires_user_confirmation is True

    # 🔒 HARD RULE: Gate-3 must not write
    assert fetch_all_memory_count() == 2


def test_no_promotion_when_already_confirmed():
    seed_memory(
        source="user_confirmed",
        promotion_gate=3,
    )

    entry = make_entry("m4")

    result = propose_memory(entry)

    assert result.promotion_decision == PromotionDecision.NO_PROMOTION
    assert fetch_all_memory_count() == 1