from typing import List
from uncertainty_engine.enums import Context
from uncertainty_engine.errors import AmbiguousContextError


KEYWORDS = {
    Context.LEARNING: ["learn", "understand", "study"],
    Context.CODE_REVIEW: ["code", "review", "refactor"],
    Context.ARCHITECTURE_DESIGN: ["architecture", "system", "design"],
    Context.PROBLEM_SOLVING: ["bug", "error", "fix", "issue"],
    Context.DECISION_MAKING: ["choose", "decide", "compare"],
    Context.PLANNING: ["plan", "roadmap", "timeline"],
    Context.EVALUATION: ["evaluate", "judge", "quality"],
}

PRIORITY_ORDER = [
    Context.CODE_REVIEW,
    Context.ARCHITECTURE_DESIGN,
    Context.PROBLEM_SOLVING,
    Context.DECISION_MAKING,
    Context.PLANNING,
    Context.EVALUATION,
    Context.LEARNING,
]


def classify_context(text: str) -> Context:
    text_lower = text.lower()
    matches: List[Context] = []

    # 1. Detect matching contexts
    for context, keywords in KEYWORDS.items():
        for word in keywords:
            if word in text_lower:
                matches.append(context)
                break

    # 2. No matches → default safely to LEARNING
    if len(matches) == 0:
        return Context.LEARNING

    # 3. Single match → safe
    if len(matches) == 1:
        return matches[0]

    # 4. Multiple matches → resolve by strict priority
    for context in PRIORITY_ORDER:
        if context in matches:
            return context

    # 5. STILL ambiguous → HARD FAIL (this is the rule you asked about)
    raise AmbiguousContextError(matches)