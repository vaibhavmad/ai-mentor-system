import pytest

from llm_executor.prompt_builder import build_prompt
from llm_executor.models import LLMRequest
from pacing_controller.enums import PacingMode
from llm_executor.errors import LLMExecutionError


# ---------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------

def _base_request(**overrides):
    data = dict(
        system_instruction="Explain the concept clearly.",
        user_content="What is dependency injection?",
        pacing_mode=PacingMode.NORMAL,
        token_limit=1000,
        forbidden_patterns=["Use percentages", "Store memory"],
        claim_label_required=False,
        turn_index=None,
    )
    data.update(overrides)
    return LLMRequest(**data)


# ---------------------------------------------------------------------
# Core structure tests
# ---------------------------------------------------------------------

def test_prompt_contains_all_four_blocks_in_order():
    request = _base_request()

    prompt = build_prompt(request)

    # Expected block markers (order matters)
    idx_system = prompt.find("You are a constrained execution engine.")
    idx_mode = prompt.find("NORMAL MODE")
    idx_forbidden = prompt.find("You must NOT:")
    idx_task = prompt.find("Task:")

    assert idx_system != -1
    assert idx_mode != -1
    assert idx_forbidden != -1
    assert idx_task != -1

    assert idx_system < idx_mode < idx_forbidden < idx_task


# ---------------------------------------------------------------------
# Mode block tests
# ---------------------------------------------------------------------

def test_normal_mode_block_content():
    request = _base_request(pacing_mode=PacingMode.NORMAL)
    prompt = build_prompt(request)

    assert "NORMAL MODE" in prompt
    assert "Target: 1000 tokens. Hard cap: 1200 tokens." in prompt
    assert "Do not split across turns." in prompt


def test_careful_mode_block_content():
    request = _base_request(pacing_mode=PacingMode.CAREFUL)
    prompt = build_prompt(request)

    assert "CAREFUL MODE" in prompt
    assert "Target: 3000 tokens. Hard cap: 5000 tokens." in prompt
    assert "Do not split across turns." in prompt


def test_deliberative_mode_injects_turn_index():
    request = _base_request(
        pacing_mode=PacingMode.DELIBERATIVE,
        turn_index=2,
    )
    prompt = build_prompt(request)

    assert "DELIBERATIVE MODE" in prompt
    assert "This is turn 2 of a multi-turn reasoning process." in prompt
    assert "end your response with: [CONTINUE]" in prompt


def test_deliberative_mode_without_turn_index_raises():
    request = _base_request(pacing_mode=PacingMode.DELIBERATIVE)

    with pytest.raises(LLMExecutionError):
        build_prompt(request)


# ---------------------------------------------------------------------
# Forbidden patterns block tests
# ---------------------------------------------------------------------

def test_forbidden_patterns_are_injected_verbatim():
    patterns = [
        "Use percentages in choices",
        "Use authoritative language",
        "Make unlabeled claims",
    ]

    request = _base_request(forbidden_patterns=patterns)
    prompt = build_prompt(request)

    assert "You must NOT:" in prompt
    for pattern in patterns:
        assert f"- {pattern}" in prompt


# ---------------------------------------------------------------------
# Task block tests
# ---------------------------------------------------------------------

def test_task_block_contains_system_instruction_and_user_content():
    request = _base_request(
        system_instruction="Do exactly this.",
        user_content="User provided input text.",
    )

    prompt = build_prompt(request)

    assert "Task:" in prompt
    assert "Do exactly this." in prompt
    assert "User input:" in prompt
    assert "User provided input text." in prompt