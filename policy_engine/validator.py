from policy_engine.errors import PolicyValidationError
from policy_engine.constants import (
    REQUIRED_VERSION,
    REQUIRED_STATUS,
    REQUIRED_CONTRACT,
    REQUIRED_DRIFT_FORBIDDEN,
)

REQUIRED_TOP_LEVEL_KEYS = [
    "version",
    "status",
    "contract",
    "driftforbidden",
    "non_negotiable_rules",
    "claim_confidence",
    "memory",
    "uncertainty",
    "groundingprotocol",
    "pacing",
    "llmexecutor",
    "outputvalidation",
    "error_messages",
    "bootvalidation",
]


def validate_policy(policy: dict) -> None:
    # STEP 4.1 — Required top-level keys
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in policy:
            raise PolicyValidationError(
                section="top-level",
                expected=f"Key '{key}' must exist",
                found="Missing key",
                context=f"policy.{key}",
            )

    # STEP 4.2 — Exact value enforcement
    if policy["version"] != REQUIRED_VERSION:
        raise PolicyValidationError(
            section="version",
            expected=REQUIRED_VERSION,
            found=str(policy["version"]),
            context="policy.version",
        )

    if policy["status"] != REQUIRED_STATUS:
        raise PolicyValidationError(
            section="status",
            expected=REQUIRED_STATUS,
            found=str(policy["status"]),
            context="policy.status",
        )

    if policy["contract"] != REQUIRED_CONTRACT:
        raise PolicyValidationError(
            section="contract",
            expected=REQUIRED_CONTRACT,
            found=str(policy["contract"]),
            context="policy.contract",
        )

    if policy["driftforbidden"] != REQUIRED_DRIFT_FORBIDDEN:
        raise PolicyValidationError(
            section="driftforbidden",
            expected=str(REQUIRED_DRIFT_FORBIDDEN),
            found=str(policy["driftforbidden"]),
            context="policy.driftforbidden",
        )
    
    # STEP 4.A.3 — Non-negotiable rules
    rules = policy.get("non_negotiable_rules")

    if not isinstance(rules, list):
        raise PolicyValidationError(
            section="non_negotiable_rules",
            expected="non_negotiable_rules must be a list",
            found=str(type(rules)),
            context="policy.non_negotiable_rules",
        )

    if len(rules) < 5:
        raise PolicyValidationError(
            section="non_negotiable_rules",
            expected="At least 5 non-negotiable rules",
            found=str(len(rules)),
            context="policy.non_negotiable_rules",
        )

    # STEP 5 — Bootvalidation.required_sections
    required_sections = policy.get("bootvalidation", {}).get("required_sections", [])
    for section in required_sections:
        if section not in policy:
            raise PolicyValidationError(
                section="bootvalidation.required_sections",
                expected=f"Section '{section}' must exist",
                found="Missing section",
                context=f"policy.{section}",
            )

    # STEP 6 — Context completeness
    params_by_context = policy["memory"].get("requiredparametersbycontext", {})
    questions_by_context = policy["groundingprotocol"].get("questions", {})

    for context in params_by_context:
        if context not in questions_by_context:
            raise PolicyValidationError(
                section="context_completeness",
                expected=f"Grounding questions for context '{context}'",
                found="Missing context",
                context=f"groundingprotocol.questions.{context}",
            )

    for context in questions_by_context:
        if context not in params_by_context:
            raise PolicyValidationError(
                section="context_completeness",
                expected=f"Required parameters for context '{context}'",
                found="Missing context",
                context=f"memory.requiredparametersbycontext.{context}",
            )

    # STEP 4.A.1 — Grounding protocol hard rule
    grounding = policy["groundingprotocol"]

    if grounding.get("numquestions") != 5:
        raise PolicyValidationError(
            section="groundingprotocol.numquestions",
            expected="numquestions must be exactly 5",
            found=str(grounding.get("numquestions")),
            context="groundingprotocol.numquestions",
        )

    questions_by_context = grounding.get("questions", {})
    for context, questions in questions_by_context.items():
        if not isinstance(questions, list):
            raise PolicyValidationError(
                section="groundingprotocol.questions",
                expected="List of questions",
                found=str(type(questions)),
                context=f"groundingprotocol.questions.{context}",
            )

        if len(questions) != 5:
            raise PolicyValidationError(
                section="groundingprotocol.questions",
                expected="Exactly 5 questions",
                found=str(len(questions)),
                context=f"groundingprotocol.questions.{context}",
            )

    sixth_rule = grounding.get("sixthquestionrule")
    if not sixth_rule:
        raise PolicyValidationError(
            section="groundingprotocol.sixthquestionrule",
            expected="sixthquestionrule block",
            found="Missing",
            context="groundingprotocol.sixthquestionrule",
        )

    if "decision_logic" not in sixth_rule or "examples" not in sixth_rule:
        raise PolicyValidationError(
            section="groundingprotocol.sixthquestionrule",
            expected="decision_logic and examples",
            found="Incomplete definition",
            context="groundingprotocol.sixthquestionrule",
        )

    # STEP 8 — Pacing rules
    pacing = policy.get("pacing", {})
    modes = pacing.get("modes", {})

    for mode_name, mode in modes.items():
        if "targettokens" not in mode:
            raise PolicyValidationError(
                section="pacing.modes",
                expected="targettokens",
                found="Missing",
                context=f"pacing.modes.{mode_name}.targettokens",
            )

        if "hardcap" not in mode:
            raise PolicyValidationError(
                section="pacing.modes",
                expected="hardcap",
                found="Missing",
                context=f"pacing.modes.{mode_name}.hardcap",
            )

        if "multiturn" not in mode:
            raise PolicyValidationError(
                section="pacing.modes",
                expected="multiturn",
                found="Missing",
                context=f"pacing.modes.{mode_name}.multiturn",
            )

        if mode["hardcap"] > 5000:
            raise PolicyValidationError(
                section="pacing.modes",
                expected="hardcap ≤ 5000",
                found=str(mode["hardcap"]),
                context=f"pacing.modes.{mode_name}.hardcap",
            )

        if mode["targettokens"] > mode["hardcap"]:
            raise PolicyValidationError(
                section="pacing.modes",
                expected="targettokens ≤ hardcap",
                found=str(mode["targettokens"]),
                context=f"pacing.modes.{mode_name}.targettokens",
            )

    # STEP 9 — Memory system rules (STRUCTURAL ONLY, for now)
    memory = policy.get("memory", {})

    decay = memory.get("decay")
    if not decay or "days" not in decay:
        raise PolicyValidationError(
            section="memory.decay",
            expected="decay.days",
            found="Missing",
            context="memory.decay.days",
        )

    if decay["days"] != 180:
        raise PolicyValidationError(
            section="memory.decay",
            expected="decay.days must be exactly 180",
            found=str(decay.get("days")),
            context="memory.decay.days",
        )
    
    if "reconfirmation_message" not in decay:
        raise PolicyValidationError(
            section="memory.decay",
            expected="reconfirmation_message must exist",
            found="Missing",
            context="memory.decay.reconfirmation_message",
        )

    promotion = memory.get("promotion")
    if not promotion or not all(g in promotion for g in ["gate1", "gate2", "gate3"]):
        raise PolicyValidationError(
            section="memory.promotion",
            expected="gate1, gate2, and gate3",
            found="Incomplete promotion gates",
            context="memory.promotion",
        )

    conflict = memory.get("conflict_resolution")
    if not conflict or "behavior" not in conflict:
        raise PolicyValidationError(
            section="memory.conflict_resolution",
            expected="conflict resolution behavior rules",
            found="Missing",
            context="memory.conflict_resolution.behavior",
        )

    # STEP 10 — Uncertainty system
    uncertainty = policy.get("uncertainty", {})

    binary_checks = uncertainty.get("binarychecks")
    if not isinstance(binary_checks, list) or len(binary_checks) != 3:
        raise PolicyValidationError(
            section="uncertainty.binarychecks",
            expected="Exactly 3 binary checks",
            found=str(binary_checks),
            context="uncertainty.binarychecks",
        )

    mapping = uncertainty.get("mapping")
    if not mapping:
        raise PolicyValidationError(
            section="uncertainty.mapping",
            expected="Uncertainty mapping definitions",
            found="Missing",
            context="uncertainty.mapping",
        )

    for key in ["allyes", "oneno", "twoormoreno"]:
        if key not in mapping:
            raise PolicyValidationError(
                section="uncertainty.mapping",
                expected=f"Mapping for '{key}'",
                found="Missing",
                context=f"uncertainty.mapping.{key}",
            )

        # STEP 4.A.4 — Error code completeness (STRICT)
    error_messages = policy.get("error_messages", {})

    if not isinstance(error_messages, dict) or not error_messages:
        raise PolicyValidationError(
            section="error_messages",
            expected="Non-empty error_messages dictionary",
            found=str(error_messages),
            context="error_messages",
        )

    referenced_codes = set()

    # from outputvalidation.mustcheck
    output_checks = policy.get("outputvalidation", {}).get("mustcheck", [])
    for code in output_checks:
        referenced_codes.add(code)

    # from validator hardcoded test expectations
    TEST_REFERENCED_CODES = {
        "missing_confidence_label",
        "percentage_in_choice",
        "intent_not_addressed",
        "assumptions_not_surfaced",
        "memory_write_without_confirmation",
        "uncertainty_not_disclosed",
        "next_steps_not_clear",
        "token_cap_reached",
        "memory_without_scope",
        "contradicts_memory",
    }

    referenced_codes.update(TEST_REFERENCED_CODES)

    for code in referenced_codes:
        if code not in error_messages:
            raise PolicyValidationError(
                section="error_messages",
                expected=f"Error message for '{code}'",
                found="Missing",
                context=f"error_messages.{code}",
            )

    return None

