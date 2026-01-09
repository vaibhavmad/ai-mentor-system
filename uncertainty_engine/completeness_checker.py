from uncertainty_engine.enums import Context, BinaryCheck

# Source of truth: required parameters per context
REQUIRED_PARAMS = {
    Context.LEARNING: ["topic", "depthorgoal"],
    Context.CODE_REVIEW: ["code", "reviewgoal"],
    Context.ARCHITECTURE_DESIGN: ["system", "goal"],
    Context.PROBLEM_SOLVING: ["problem"],
    Context.DECISION_MAKING: ["criteria", "constraints"],
    Context.PLANNING: ["goal", "timehorizon"],
    Context.EVALUATION: ["subject", "standard"],
}


def param_is_present(context: Context, param: str, text: str) -> bool:
    t = text.lower()

    if context == Context.LEARNING:
        if param == "topic":
            return len(t.split()) >= 2
        if param == "depthorgoal":
            return any(w in t for w in ["overview", "deep", "master", "learn"])

    if context == Context.CODE_REVIEW:
        if param == "code":
            return "```" in text
        if param == "reviewgoal":
            return any(w in t for w in ["review", "improve", "optimize", "refactor"])

    if context == Context.ARCHITECTURE_DESIGN:
        if param == "system":
            return any(w in t for w in ["system", "architecture", "service"])
        if param == "goal":
            return any(w in t for w in ["goal", "want", "to ", "so that"])

    if context == Context.PROBLEM_SOLVING:
        return any(w in t for w in ["error", "bug", "fails", "issue"])

    if context == Context.DECISION_MAKING:
        if param == "criteria":
            return any(w in t for w in ["criteria", "based on", "priority"])
        if param == "constraints":
            return any(w in t for w in ["must", "cannot", "limited"])

    if context == Context.PLANNING:
        if param == "goal":
            return any(w in t for w in ["build", "launch", "achieve"])
        if param == "timehorizon":
            return any(w in t for w in ["week", "month", "year", "days"])

    if context == Context.EVALUATION:
        if param == "subject":
            return len(t.split()) >= 2
        if param == "standard":
            return any(w in t for w in ["better", "quality", "compare"])

    return False


def check_completeness(context: Context, text: str) -> BinaryCheck:
    required = REQUIRED_PARAMS.get(context, [])

    for param in required:
        if not param_is_present(context, param, text):
            return BinaryCheck.NO  # EARLY FAIL

    return BinaryCheck.YES