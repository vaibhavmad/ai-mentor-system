from dataclasses import dataclass

@dataclass(frozen=True)
class PacingLimits:
    target_tokens: int
    hard_cap_tokens: int
    multiturn: bool

@dataclass(frozen=True)
class PacingDecision:
    accepted: bool
    must_continue_in_next_turn: bool
    reason: str