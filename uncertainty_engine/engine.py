from uncertainty_engine.context_classifier import classify_context
from uncertainty_engine.intent_checker import check_intent
from uncertainty_engine.completeness_checker import check_completeness
from uncertainty_engine.memory_checker import check_memory_consistency
from uncertainty_engine.matrix import map_to_level
from uncertainty_engine.reason_templates import REASONS
from uncertainty_engine.models import (
    BinaryCheckResult,
    UncertaintyAssessment,
)
from uncertainty_engine.enums import (
    BinaryCheck,
    UncertaintyLevel,
)
from memory_manager.enums import MemoryQueryResult


class UncertaintyEngine:
    def assess(
        self,
        user_input: str,
        memory_query_result: MemoryQueryResult,
    ) -> UncertaintyAssessment:
        """
        Deterministically assess uncertainty for a single user input.
        No checks may be skipped. No inference is allowed.
        """

        # 1. Context classification (MUST be first)
        context = classify_context(user_input)

        # 2. Intent clarity check
        intent_clarity = check_intent(user_input)

        # 3. Context completeness check
        # Only expected completeness failures are converted to NO
        try:
            context_completeness = check_completeness(context, user_input)
        except ValueError:
            context_completeness = BinaryCheck.NO

        # 4. Memory consistency check
        memory_consistency = check_memory_consistency(memory_query_result)

        # 5. Assemble binary checks
        checks = BinaryCheckResult(
            intent_clarity=intent_clarity,
            context_completeness=context_completeness,
            memory_consistency=memory_consistency,
        )

        # 6. Matrix mapping (FULL, NO SHORTCUTS)
        level = map_to_level(checks)

        # 7. Build deterministic reasons (2–5 only)
        reasons = []

        # Intent reason
        if intent_clarity == BinaryCheck.YES:
            reasons.append(REASONS["intent_clear"])
        else:
            reasons.append(REASONS["intent_vague"])

        # Context completeness reason
        if context_completeness == BinaryCheck.YES:
            reasons.append(
                REASONS["context_complete"].format(context=context.value)
            )
        else:
            reasons.append(REASONS["ask_context"])

        # Memory consistency reason
        if memory_consistency == BinaryCheck.YES:
            reasons.append(REASONS["memory_ok"])
        else:
            reasons.append(REASONS["memory_conflict"])

        # Level-based action reason (STRICT MATRIX COMPLIANCE)
        if level == UncertaintyLevel.LEVEL_1_2:
            reasons.append(REASONS["proceed"])

        elif level == UncertaintyLevel.LEVEL_3:
            if intent_clarity == BinaryCheck.NO:
                reasons.append(REASONS["ask_intent"])
            elif context_completeness == BinaryCheck.NO:
                reasons.append(REASONS["ask_context"])
            else:
                reasons.append(REASONS["resolve_memory"])

        elif level == UncertaintyLevel.LEVEL_4:
            if intent_clarity == BinaryCheck.NO:
                reasons.append(REASONS["ask_intent"])
            if context_completeness == BinaryCheck.NO:
                reasons.append(REASONS["ask_context"])
            if memory_consistency == BinaryCheck.NO:
                reasons.append(REASONS["resolve_memory"])

        else:  # LEVEL_5
            reasons.append(REASONS["blocked"])

        # Enforce deterministic upper bound
        reasons = reasons[:5]

        return UncertaintyAssessment(
            context=context,
            checks=checks,
            level=level,
            reasons=reasons,
        )