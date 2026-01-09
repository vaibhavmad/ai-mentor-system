from llm_executor.models import LLMRequest
from pacing_controller.enums import PacingMode
from llm_executor.errors import LLMExecutionError


SYSTEM_CONTROL_BLOCK = """
You are a constrained execution engine.

You MUST:
- Follow instructions exactly
- Respect token limits
- Obey all constraints below

You MUST NOT:
- Make decisions
- Store memory
- Change scope
- Invent rules
""".strip()


def _build_mode_block(mode: PacingMode, turn_index: int | None) -> str:
    if mode == PacingMode.NORMAL:
        return """
NORMAL MODE
Produce a concise response.
Target: 1000 tokens. Hard cap: 1200 tokens.
Do not split across turns.
""".strip()

    if mode == PacingMode.CAREFUL:
        return """
CAREFUL MODE
Produce a detailed response.
Target: 3000 tokens. Hard cap: 5000 tokens.
Do not split across turns.
""".strip()

    if mode == PacingMode.DELIBERATIVE:
        if turn_index is None:
            raise LLMExecutionError(
                "turn_index must be provided for DELIBERATIVE mode"
            )

        return f"""
DELIBERATIVE MODE
This is turn {turn_index} of a multi-turn reasoning process.
Target: 1200 tokens. Hard cap: 1200 tokens.
If more work remains, end your response with: [CONTINUE]
Do not exceed the limit.
""".strip()

    raise LLMExecutionError(f"Unknown pacing mode: {mode}")


def _build_forbidden_block(forbidden_patterns: list[str]) -> str:
    lines = ["You must NOT:"]
    for pattern in forbidden_patterns:
        lines.append(f"- {pattern}")
    return "\n".join(lines)


def _build_task_block(system_instruction: str, user_content: str) -> str:
    return f"""
Task:
{system_instruction}

User input:
{user_content}
""".strip()


def build_prompt(request: LLMRequest) -> str:
    """
    Build the final prompt sent to the LLM.

    EXACT structure (fixed, non-negotiable):
    1. System control block
    2. Mode block
    3. Forbidden patterns block
    4. Task block
    """

    if request is None:
        raise LLMExecutionError("LLMRequest must not be None")

    blocks = [
        SYSTEM_CONTROL_BLOCK,
        _build_mode_block(request.pacing_mode, request.turn_index),
        _build_forbidden_block(request.forbidden_patterns),
        _build_task_block(request.system_instruction, request.user_content),
    ]

    return "\n\n".join(blocks)