import re
from typing import Optional, Tuple

CONFIDENCE_LABELS = ["[HIGH]", "[MEDIUM]", "[LOW]"]

ASSERTIVE_TERMS = [
    " is ",
    " are ",
    " will ",
    " must ",
    " definitely ",
    " certainly ",
    " guaranteed ",
    " works ",
    " means ",
]

LOW_ASSERTIVE_TERMS = [
    " definitely ",
    " will ",
    " must ",
    " guaranteed ",
    " you should ",
]

AUTHORITY_PHRASES = [
    "you must",
    "you should",
    "this is the only way",
    "without doubt",
    "clearly",
    "undeniably",
]

PERCENT_PATTERN = re.compile(r"\d+\s*%")
CHOICE_PATTERN = re.compile(r"\b([A-C])\)")

# ------------------------------------------------------------------
# Claim confidence labeling
# ------------------------------------------------------------------

def contains_claim_without_label(text: str) -> bool:
    sentences = re.split(r"[.\n]", text)
    for sentence in sentences:
        s = sentence.strip().lower()
        if not s:
            continue

        # Only evaluate assertive claims
        if any(term in s for term in ASSERTIVE_TERMS):
            if not any(label in sentence for label in CONFIDENCE_LABELS):
                return True
    return False


def low_confidence_asserted(text: str) -> bool:
    lines = text.splitlines()
    for line in lines:
        if "[LOW]" in line:
            lower = line.lower()
            if any(term in lower for term in LOW_ASSERTIVE_TERMS):
                return True
    return False


# ------------------------------------------------------------------
# Choice formatting rules
# ------------------------------------------------------------------

def violates_abc_rules(text: str) -> Tuple[bool, Optional[str]]:
    if PERCENT_PATTERN.search(text):
        return True, "percentageinchoice"

    choices = CHOICE_PATTERN.findall(text)
    if choices:
        normalized = sorted(c.upper() for c in choices)
        if normalized != ["A", "B", "C"]:
            return True, "invaliduserchoiceformat"

    return False, None


# ------------------------------------------------------------------
# Authority language
# ------------------------------------------------------------------

def contains_forbidden_authority(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in AUTHORITY_PHRASES)


# ------------------------------------------------------------------
# Question detection
# ------------------------------------------------------------------

def contains_clarifying_question(text: str) -> bool:
    return "?" in text


def contains_grounding_questions(text: str) -> bool:
    return text.count("?") >= 3


# ------------------------------------------------------------------
# Assumptions & uncertainty
# ------------------------------------------------------------------

def contains_assumption_block(text: str) -> bool:
    lower = text.lower()
    return "i assume" in lower or "assumption" in lower


def contains_uncertainty_language(text: str) -> bool:
    lower = text.lower()
    return any(
        word in lower
        for word in ["might", "uncertain", "not sure", "possibly", "depends"]
    )


# ------------------------------------------------------------------
# Next steps
# ------------------------------------------------------------------

def contains_next_steps_or_explicit_stop(text: str) -> bool:
    lower = text.lower()
    return (
        "next step" in lower
        or "you can now" in lower
        or "we should" in lower
        or "let me know" in lower
        or "stop here" in lower
    )


# ------------------------------------------------------------------
# Intent matching
# ------------------------------------------------------------------

def addresses_user_intent(text: str, intent: str) -> bool:
    intent_keywords = [
        word.lower() for word in re.split(r"\W+", intent) if word
    ]
    lower = text.lower()
    hits = sum(1 for word in intent_keywords if word in lower)
    return hits >= 1