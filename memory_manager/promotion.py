from typing import List

from memory_manager.enums import PromotionDecision
from memory_manager.models import MemoryEntry, ProposalResult


def evaluate_promotion(
    existing_entries: List[MemoryEntry],
    proposed_entry: MemoryEntry,
) -> ProposalResult:
    """
    Full 3-gate promotion logic.
    """

    if not existing_entries:
        proposed_entry = MemoryEntry(
            **{**proposed_entry.__dict__, "promotion_gate": 1}
        )
        return ProposalResult(
            proposed_entry=proposed_entry,
            promotion_decision=PromotionDecision.GATE_1_OBSERVE,
            requires_user_confirmation=False,
            message_to_user="Noted for now. I’ll observe this before saving it.",
        )

    same_context = [
        e for e in existing_entries if e.context == proposed_entry.context
    ]
    different_context = [
        e for e in existing_entries if e.context != proposed_entry.context
    ]

    # Gate 2: repetition across different contexts
    if different_context and not same_context:
        proposed_entry = MemoryEntry(
            **{**proposed_entry.__dict__, "promotion_gate": 2}
        )
        return ProposalResult(
            proposed_entry=proposed_entry,
            promotion_decision=PromotionDecision.GATE_2_FLAG,
            requires_user_confirmation=False,
            message_to_user="I’ve seen this preference across contexts. I’ll flag it for now.",
        )

    # Gate 3: same context across ≥3 sessions
    if len(same_context) >= 2:
        proposed_entry = MemoryEntry(
            **{**proposed_entry.__dict__, "promotion_gate": 3}
        )
        return ProposalResult(
            proposed_entry=proposed_entry,
            promotion_decision=PromotionDecision.GATE_3_REQUIRE_CONFIRMATION,
            requires_user_confirmation=True,
            message_to_user="I’ve seen this repeatedly in the same context. Should I remember this?",
        )

    # Default: no promotion yet
    proposed_entry = MemoryEntry(
        **{**proposed_entry.__dict__, "promotion_gate": 1}
    )
    return ProposalResult(
        proposed_entry=proposed_entry,
        promotion_decision=PromotionDecision.NO_PROMOTION,
        requires_user_confirmation=False,
        message_to_user="I’ve noted this, but won’t store it yet.",
    )