from uncertainty_engine.enums import BinaryCheck, UncertaintyLevel
from uncertainty_engine.models import BinaryCheckResult


def map_to_level(checks: BinaryCheckResult) -> UncertaintyLevel:
    no_count = sum([
        checks.intent_clarity == BinaryCheck.NO,
        checks.context_completeness == BinaryCheck.NO,
        checks.memory_consistency == BinaryCheck.NO,
    ])

    if no_count == 0:
        return UncertaintyLevel.LEVEL_1_2

    if no_count == 1:
        return UncertaintyLevel.LEVEL_3

    if no_count == 2:
        return UncertaintyLevel.LEVEL_4

    return UncertaintyLevel.LEVEL_5