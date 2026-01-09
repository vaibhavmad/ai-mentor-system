from dataclasses import dataclass
from typing import List, Optional

from pacing_controller.enums import PacingMode


@dataclass(frozen=True)
class LLMRequest:
    """
    Immutable request object passed into the LLMExecutor.

    This object contains ONLY explicit instructions.
    No defaults, no inference, no decision-making.
    """

    system_instruction: str
    user_content: str
    pacing_mode: PacingMode
    token_limit: int
    forbidden_patterns: List[str]
    claim_label_required: bool
    turn_index: Optional[int] = None  # Used only for DELIBERATIVE mode


@dataclass(frozen=True)
class LLMResponse:
    """
    Immutable response returned by the LLMExecutor.

    This is a raw execution result.
    No validation, no interpretation, no modification.
    """

    text: str
    token_usage_input: int
    token_usage_output: int
    model_name: str
    raw_provider_response: dict