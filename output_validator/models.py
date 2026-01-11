from dataclasses import dataclass
from enum import Enum
from typing import Optional, Literal


class ErrorCode(Enum):
    missing_confidence_label = "missing_confidence_label"
    low_confidence_asserted = "low_confidence_asserted"
    percentage_in_choice = "percentage_in_choice"
    invalid_user_choice_format = "invalid_user_choice_format"
    assumptions_not_surfaced = "assumptions_not_surfaced"
    proceeded_with_uncertainty3 = "proceeded_with_uncertainty3"
    proceeded_with_uncertainty45 = "proceeded_with_uncertainty45"
    memory_write_without_confirmation = "memory_write_without_confirmation"
    memory_without_scope = "memory_without_scope"
    token_cap_reached = "token_cap_reached"
    next_steps_not_clear = "next_steps_not_clear"
    uncertainty_not_disclosed = "uncertainty_not_disclosed"
    intent_not_addressed = "intent_not_addressed"
    forbidden_authoritative_phrasing = "forbidden_authoritative_phrasing"
    contradicts_memory = "contradicts_memory"


@dataclass(frozen=True)
class ValidationResult:
    status: Literal["ACCEPTED", "REJECTED"]
    error_code: Optional[ErrorCode]
    message: Optional[str]

    def __post_init__(self):
        # Enforce invariant:
        # error_code is None ONLY if status == "ACCEPTED"
        if self.status == "ACCEPTED" and self.error_code is not None:
            raise ValueError(
                "ValidationResult with status ACCEPTED must not have an error_code"
            )

        if self.status == "REJECTED" and self.error_code is None:
            raise ValueError(
                "ValidationResult with status REJECTED must have an error_code"
            )