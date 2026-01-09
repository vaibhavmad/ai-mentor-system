from uncertainty_engine.enums import BinaryCheck
from memory_manager.enums import MemoryQueryResult


def check_memory_consistency(result: MemoryQueryResult) -> BinaryCheck:
    if result == MemoryQueryResult.CONFLICT:
        return BinaryCheck.NO

    return BinaryCheck.YES