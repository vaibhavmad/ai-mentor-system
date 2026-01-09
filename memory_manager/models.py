from dataclasses import dataclass
from datetime import datetime

from memory_manager.enums import DecayStatus, PromotionDecision


@dataclass(frozen=True)
class MemoryEntry:
    id: str
    context: str
    content: str
    confidence_level: str          # HIGH | MEDIUM | LOW
    source: str                    # observed | user_confirmed
    promotion_gate: int            # 1, 2, or 3
    created_at: datetime
    last_used_at: datetime
    status: DecayStatus            # ACTIVE | STALE | RECONFIRMED | HISTORICAL


@dataclass(frozen=True)
class ProposalResult:
    proposed_entry: MemoryEntry
    promotion_decision: PromotionDecision
    requires_user_confirmation: bool
    message_to_user: str