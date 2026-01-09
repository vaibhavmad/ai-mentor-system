from datetime import datetime, timedelta

from memory_manager.enums import DecayStatus
from memory_manager.models import MemoryEntry
from memory_manager.errors import DecayReconfirmationRequired
from memory_manager.audit import (
    audit_memory_marked_stale,
    audit_memory_reconfirmed,
    audit_memory_marked_historical,
    audit_memory_conflict_detected,
)

DECAY_DAYS = 180


def evaluate_decay(entry: MemoryEntry) -> DecayStatus:
    age = datetime.utcnow() - entry.last_used_at
    if age > timedelta(days=DECAY_DAYS):
            audit_memory_marked_stale(entry.id)
            return DecayStatus.STALE
    return DecayStatus.ACTIVE


def handle_reconfirmation(
    entry: MemoryEntry,
    user_response: str,
) -> MemoryEntry:
    """
    Handle user response for stale memory.
    """

    if user_response == "yes":
        updated = MemoryEntry(
            **{
                **entry.__dict__,
                "status": DecayStatus.RECONFIRMED,
                "last_used_at": datetime.utcnow(),
            }
        )
        audit_memory_reconfirmed(entry.id)
        return updated

    if user_response == "no":
        updated = MemoryEntry(
            **{
                **entry.__dict__,
                "status": DecayStatus.HISTORICAL,
            }
        )
        audit_memory_marked_historical(entry.id)
        return updated

    if user_response == "unsure":
        audit_memory_conflict_detected(entry.id)
        raise DecayReconfirmationRequired(
            "User is unsure. Memory marked as conflict."
        )

    raise ValueError(f"Invalid reconfirmation response: {user_response}")