from output_validator.models import ValidationResult, ErrorCode
from output_validator.rules import (
    contains_claim_without_label,
    low_confidence_asserted,
    violates_abc_rules,
    contains_forbidden_authority,
    contains_clarifying_question,
    contains_grounding_questions,
    contains_assumption_block,
    contains_uncertainty_language,
    contains_next_steps_or_explicit_stop,
    addresses_user_intent,
)
from orchestrator.models import OrchestratorContext
from uncertainty_engine.enums import UncertaintyLevel
from policy_engine.policy_engine import PolicyEngine


class OutputValidator:
    """
    Hard gatekeeper for LLM output.
    Enforces policy v1.3.2 deterministically and fail-fast.
    """

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    def _reject(self, error_code: ErrorCode) -> ValidationResult:
        return ValidationResult(
            status="REJECTED",
            error_code=error_code,
            message=self.policy_engine.get_error_message(error_code),
        )

    def validate(self, text: str, context: OrchestratorContext) -> ValidationResult:
        # 1️⃣ Token limit (authoritative, trust context)
        if context.token_count > context.token_limit:
            return self._reject(ErrorCode.tokencapreached)

        # 2️⃣ Missing confidence labels
        if contains_claim_without_label(text):
            return self._reject(ErrorCode.missingconfidencelabel)

        # 3️⃣ LOW confidence misuse
        if low_confidence_asserted(text):
            return self._reject(ErrorCode.lowconfidenceasserted)

        # 4️⃣ Uncertainty Level 3 rule
        if context.uncertainty_level == UncertaintyLevel.LEVEL_3:
            if not contains_clarifying_question(text):
                return self._reject(ErrorCode.proceededwithuncertainty3)

        # 5️⃣ Uncertainty Level 4–5 rule
        if context.uncertainty_level in (
            UncertaintyLevel.LEVEL_4,
            UncertaintyLevel.LEVEL_5,
        ):
            if not contains_grounding_questions(text):
                return self._reject(ErrorCode.proceededwithuncertainty45)

        # 6️⃣ A/B/C rules + percentages
        violates, error = violates_abc_rules(text)
        if violates:
            return self._reject(error)

        # 7️⃣ Assumptions surfaced
        if context.assumptions_required:
            if not contains_assumption_block(text):
                return self._reject(ErrorCode.assumptionsnotsurfaced)

        # 8️⃣ Forbidden authority language
        if contains_forbidden_authority(text):
            return self._reject(ErrorCode.forbiddenauthoritativephrasing)

        # 9️⃣ Memory safety rules (STEP 9.7)
        if context.memory_write_attempted:
            if not context.memory_confirmation_asked:
                return self._reject(ErrorCode.memorywritewithoutconfirmation)
            if not context.memory_scope:
                return self._reject(ErrorCode.memorywithoutscope)

        # 🔟 Intent addressed
        if not addresses_user_intent(text, context.user_intent):
            return self._reject(ErrorCode.intentnotaddressed)

        # 1️⃣1️⃣ Uncertainty disclosed
        if context.contains_medium_or_low_confidence_claims:
            if not contains_uncertainty_language(text):
                return self._reject(ErrorCode.uncertaintynotdisclosed)

        # 1️⃣2️⃣ Next steps clarity
        if not contains_next_steps_or_explicit_stop(text):
            return self._reject(ErrorCode.nextstepsnotclear)

        # ✅ ACCEPTED
        return ValidationResult(
            status="ACCEPTED",
            error_code=None,
            message=None,
        )