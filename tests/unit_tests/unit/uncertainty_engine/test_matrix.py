from uncertainty_engine.matrix import map_to_level
from uncertainty_engine.enums import BinaryCheck, UncertaintyLevel
from uncertainty_engine.models import BinaryCheckResult


def make_checks(intent, complete, memory):
    return BinaryCheckResult(
        intent_clarity=intent,
        context_completeness=complete,
        memory_consistency=memory,
    )


def test_all_yes_maps_to_level_1_2():
    checks = make_checks(BinaryCheck.YES, BinaryCheck.YES, BinaryCheck.YES)
    assert map_to_level(checks) == UncertaintyLevel.LEVEL_1_2


def test_single_no_intent_maps_to_level_3():
    checks = make_checks(BinaryCheck.NO, BinaryCheck.YES, BinaryCheck.YES)
    assert map_to_level(checks) == UncertaintyLevel.LEVEL_3


def test_single_no_completeness_maps_to_level_3():
    checks = make_checks(BinaryCheck.YES, BinaryCheck.NO, BinaryCheck.YES)
    assert map_to_level(checks) == UncertaintyLevel.LEVEL_3


def test_single_no_memory_maps_to_level_3():
    checks = make_checks(BinaryCheck.YES, BinaryCheck.YES, BinaryCheck.NO)
    assert map_to_level(checks) == UncertaintyLevel.LEVEL_3


def test_two_nos_maps_to_level_4():
    checks = make_checks(BinaryCheck.NO, BinaryCheck.NO, BinaryCheck.YES)
    assert map_to_level(checks) == UncertaintyLevel.LEVEL_4


def test_two_nos_with_memory_maps_to_level_4():
    checks = make_checks(BinaryCheck.NO, BinaryCheck.YES, BinaryCheck.NO)
    assert map_to_level(checks) == UncertaintyLevel.LEVEL_4


def test_two_nos_completeness_and_memory_maps_to_level_4():
    checks = make_checks(BinaryCheck.YES, BinaryCheck.NO, BinaryCheck.NO)
    assert map_to_level(checks) == UncertaintyLevel.LEVEL_4


def test_all_no_maps_to_level_5():
    checks = make_checks(BinaryCheck.NO, BinaryCheck.NO, BinaryCheck.NO)
    assert map_to_level(checks) == UncertaintyLevel.LEVEL_5