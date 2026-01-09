from dataclasses import dataclass
from typing import List

from uncertainty_engine.enums import Context, BinaryCheck, UncertaintyLevel


@dataclass(frozen=True)
class BinaryCheckResult:
    intent_clarity: BinaryCheck
    context_completeness: BinaryCheck
    memory_consistency: BinaryCheck


@dataclass(frozen=True)
class UncertaintyAssessment:
    context: Context
    checks: BinaryCheckResult
    level: UncertaintyLevel
    reasons: List[str]