from typing import List, Tuple, Optional
from datetime import datetime

from memory_manager.enums import (
    MemoryQueryResult,
    DecayStatus,
    PromotionDecision,
)
from memory_manager.models import MemoryEntry, ProposalResult
from memory_manager.errors import (
    InvalidContextError,
    ConflictUnresolvedError,
    PromotionError,
    DecayReconfirmationRequired,
)
from memory_manager.storage import get_connection
from memory_manager.promotion import evaluate_promotion
from memory_manager.conflict import is_conflict, resolve_conflict
from memory_manager.decay import evaluate_decay, handle_reconfirmation
from memory_manager.audit import (
    audit_memory_proposed,
    audit_memory_confirmed,
    audit_memory_rejected,
    audit_memory_conflict_detected,
    audit_memory_conflict_resolved,
    audit_memory_marked_stale,
    audit_memory_reconfirmed,
    audit_memory_marked_historical,
)

# ------------------------------------------------------------------
# Context rules
# ------------------------------------------------------------------

ALLOWED_CONTEXTS = {
    "learning",
    "code_review",
    "architecture_design",
    "problem_solving",
    "decision_making",
    "planning",
    "evaluation",
}


def validate_context(context: str) -> None:
    if context not in ALLOWED_CONTEXTS:
        raise InvalidContextError(
            f"Context '{context}' is invalid. Must be one of {ALLOWED_CONTEXTS}"
        )


# ------------------------------------------------------------------
# QUERY ENGINE (READ PATH)
# ------------------------------------------------------------------

def query_memory(
    context: str,
    content_key: Optional[str] = None,
) -> Tuple[MemoryQueryResult, List[MemoryEntry]]:
    """
    Deterministic read.
    If content_key is provided, performs a LIKE match on content.
    """
    validate_context(context)

    conn = get_connection()
    cursor = conn.cursor()

    if content_key:
        cursor.execute(
            """
            SELECT
                id, context, content, confidence_level, source,
                promotion_gate, created_at, last_used_at, status
            FROM memory_entries
            WHERE context = ? AND content LIKE ?
            """,
            (context, f"%{content_key}%"),
        )
    else:
        cursor.execute(
            """
            SELECT
                id, context, content, confidence_level, source,
                promotion_gate, created_at, last_used_at, status
            FROM memory_entries
            WHERE context = ?
            """,
            (context,),
        )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return MemoryQueryResult.EMPTY, []

    entries = [
        MemoryEntry(
            id=row[0],
            context=row[1],
            content=row[2],
            confidence_level=row[3],
            source=row[4],
            promotion_gate=row[5],
            created_at=datetime.fromisoformat(row[6]),
            last_used_at=datetime.fromisoformat(row[7]),
            status=DecayStatus(row[8]),
        )
        for row in rows
    ]

    if len(entries) == 1:
        return MemoryQueryResult.PRESENT, entries

    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            if is_conflict(entries[i], entries[j]):
                audit_memory_conflict_detected(entries[i].id)
                return MemoryQueryResult.CONFLICT, entries

    return MemoryQueryResult.PARTIAL, entries


# ------------------------------------------------------------------
# PROMOTION (WRITE PATH – CONTROLLED)
# ------------------------------------------------------------------

_PROMOTION_GATE_MAP = {
    PromotionDecision.GATE_1_OBSERVE: 1,
    PromotionDecision.GATE_2_FLAG: 2,
    PromotionDecision.GATE_3_REQUIRE_CONFIRMATION: 3,
}


def propose_memory(entry: MemoryEntry) -> ProposalResult:
    """
    Propose memory without committing Gate-3 promotions.
    Gate-1 and Gate-2 are persisted; Gate-3 requires confirmation.
    """
    validate_context(entry.context)

    _, existing = query_memory(entry.context)

    # Ensure promotion_gate is not set prematurely
    base_entry = MemoryEntry(
        **{
            **entry.__dict__,
            "promotion_gate": 0,
        }
    )

    result = evaluate_promotion(existing, base_entry)
    audit_memory_proposed(base_entry.id)

    # Explicit Gate-3 no-write enforcement
    if result.promotion_decision == PromotionDecision.GATE_3_REQUIRE_CONFIRMATION:
        return result

    # Persist Gate-1 / Gate-2 only
    gate = _PROMOTION_GATE_MAP.get(result.promotion_decision)
    if gate:
        to_persist = MemoryEntry(
            **{
                **result.proposed_entry.__dict__,
                "promotion_gate": gate,
            }
        )
        _persist_entry(to_persist)

    return result


def confirm_memory(entry_id: str, user_response: str) -> MemoryEntry:
    """
    Confirm a previously proposed (Gate-3) memory.
    """
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

    if not row:
        raise PromotionError("Proposed memory not found")

    entry = MemoryEntry(
        id=row[0],
        context=row[1],
        content=row[2],
        confidence_level=row[3],
        source=row[4],
        promotion_gate=row[5],
        created_at=datetime.fromisoformat(row[6]),
        last_used_at=datetime.fromisoformat(row[7]),
        status=DecayStatus(row[8]),
    )

    if user_response.lower() != "yes":
        audit_memory_rejected(entry.id)
        raise PromotionError("User rejected memory promotion")

    confirmed = MemoryEntry(
        **{
            **entry.__dict__,
            "source": "user_confirmed",
            "last_used_at": datetime.utcnow(),
            "status": DecayStatus.ACTIVE,
        }
    )

    _persist_entry(confirmed)
    audit_memory_confirmed(confirmed.id)
    return confirmed


# ------------------------------------------------------------------
# CONFLICT RESOLUTION
# ------------------------------------------------------------------

def resolve_conflict_api(
    entry_a: MemoryEntry,
    entry_b: MemoryEntry,
    choice: str,
) -> List[MemoryEntry]:
    if not is_conflict(entry_a, entry_b):
        return [entry_a]

    resolved_entries, resolved = resolve_conflict(choice, entry_a, entry_b)

    if not resolved:
        raise ConflictUnresolvedError("Conflict remains unresolved")

    for e in resolved_entries:
        audit_memory_conflict_resolved(e.id)

    return resolved_entries


# ------------------------------------------------------------------
# DECAY & RECONFIRMATION
# ------------------------------------------------------------------

def check_and_apply_decay(entry: MemoryEntry) -> MemoryEntry:
    status = evaluate_decay(entry)

    if status == DecayStatus.STALE:
        audit_memory_marked_stale(entry.id)
        raise DecayReconfirmationRequired(
            "Memory is stale and requires reconfirmation"
        )

    return entry


def apply_reconfirmation(entry: MemoryEntry, user_response: str) -> MemoryEntry:
    updated = handle_reconfirmation(entry, user_response)

    if updated.status == DecayStatus.RECONFIRMED:
        audit_memory_reconfirmed(updated.id)
    elif updated.status == DecayStatus.HISTORICAL:
        audit_memory_marked_historical(updated.id)

    _persist_entry(updated)
    return updated


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _persist_entry(entry: MemoryEntry) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO memory_entries
        (id, context, content, confidence_level, source,
         promotion_gate, created_at, last_used_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def get_active_memory(context: str) -> List[MemoryEntry]:
    validate_context(context)
    _, entries = query_memory(context)
    return [e for e in entries if e.status == DecayStatus.ACTIVE]


# ------------------------------------------------------------------
# PUBLIC FACADE — CLASS-BASED API (FOR SYSTEM WIRING & TEST HARNESS)
# ------------------------------------------------------------------

class MemoryManager:
    """
    Thin facade over the Memory Manager module-level API.

    PURPOSE:
    - Provide a class-based public interface
    - Preserve existing functional implementation
    - Enable deterministic system wiring and testing

    HARD RULES:
    - No internal state
    - No logic added
    - No behavior changes
    - Delegates ONLY to canonical functions
    """

    def query_memory(
        self,
        context: str,
        content_key: Optional[str] = None,
    ) -> Tuple[MemoryQueryResult, List[MemoryEntry]]:
        return query_memory(context, content_key)

    def propose_memory(self, entry: MemoryEntry) -> ProposalResult:
        return propose_memory(entry)

    def confirm_memory(self, entry_id: str, user_response: str) -> MemoryEntry:
        return confirm_memory(entry_id, user_response)

    def resolve_conflict(
        self,
        entry_a: MemoryEntry,
        entry_b: MemoryEntry,
        choice: str,
    ) -> List[MemoryEntry]:
        return resolve_conflict_api(entry_a, entry_b, choice)

    def check_and_apply_decay(self, entry: MemoryEntry) -> MemoryEntry:
        return check_and_apply_decay(entry)

    def apply_reconfirmation(
        self,
        entry: MemoryEntry,
        user_response: str,
    ) -> MemoryEntry:
        return apply_reconfirmation(entry, user_response)

    def get_active_memory(self, context: str) -> List[MemoryEntry]:
        return get_active_memory(context)