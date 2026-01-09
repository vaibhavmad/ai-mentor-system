from uncertainty_engine.memory_checker import check_memory_consistency
from uncertainty_engine.enums import BinaryCheck
from memory_manager.enums import MemoryQueryResult


def test_memory_empty_is_safe():
    result = check_memory_consistency(MemoryQueryResult.EMPTY)
    assert result == BinaryCheck.YES


def test_memory_partial_is_safe():
    result = check_memory_consistency(MemoryQueryResult.PARTIAL)
    assert result == BinaryCheck.YES


def test_memory_present_is_safe():
    result = check_memory_consistency(MemoryQueryResult.PRESENT)
    assert result == BinaryCheck.YES


def test_memory_conflict_is_unsafe():
    result = check_memory_consistency(MemoryQueryResult.CONFLICT)
    assert result == BinaryCheck.NO