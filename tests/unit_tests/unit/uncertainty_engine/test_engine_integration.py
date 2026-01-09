import pytest

from uncertainty_engine.engine import UncertaintyEngine
from uncertainty_engine.enums import (
    Context,
    BinaryCheck,
    UncertaintyLevel,
)
from uncertainty_engine.reason_templates import REASONS
from memory_manager.enums import MemoryQueryResult


engine = UncertaintyEngine()


def test_fully_valid_input_proceeds():
    text = "I want to learn Python at a deep level"
    result = engine.assess(text, MemoryQueryResult.EMPTY)

    assert result.context == Context.LEARNING
    assert result.level == UncertaintyLevel.LEVEL_1_2

    assert result.checks.intent_clarity == BinaryCheck.YES
    assert result.checks.context_completeness == BinaryCheck.YES
    assert result.checks.memory_consistency == BinaryCheck.YES

    assert REASONS["proceed"] in result.reasons


def test_vague_intent_triggers_level_3():
    text = "Help me"
    result = engine.assess(text, MemoryQueryResult.EMPTY)

    assert result.level == UncertaintyLevel.LEVEL_3
    assert result.checks.intent_clarity == BinaryCheck.NO
    assert REASONS["ask_intent"] in result.reasons


def test_missing_context_triggers_level_3():
    text = "I want to learn Python"
    result = engine.assess(text, MemoryQueryResult.EMPTY)

    assert result.level == UncertaintyLevel.LEVEL_3
    assert result.checks.context_completeness == BinaryCheck.NO
    assert REASONS["ask_context"] in result.reasons


def test_memory_conflict_triggers_level_3_or_higher():
    text = "I want to learn Python at a deep level"
    result = engine.assess(text, MemoryQueryResult.CONFLICT)

    assert result.checks.memory_consistency == BinaryCheck.NO
    assert result.level in {
        UncertaintyLevel.LEVEL_3,
        UncertaintyLevel.LEVEL_4,
        UncertaintyLevel.LEVEL_5,
    }
    assert REASONS["memory_conflict"] in result.reasons


def test_multiple_failures_triggers_level_5():
    text = "Help me fix this"
    result = engine.assess(text, MemoryQueryResult.CONFLICT)

    assert result.level == UncertaintyLevel.LEVEL_5
    assert REASONS["blocked"] in result.reasons