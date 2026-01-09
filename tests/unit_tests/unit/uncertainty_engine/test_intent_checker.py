import pytest

from uncertainty_engine.intent_checker import check_intent
from uncertainty_engine.enums import BinaryCheck


def test_intent_clear_simple_statement():
    text = "I want to learn Python error handling"
    result = check_intent(text)
    assert result == BinaryCheck.YES


def test_intent_vague_make_it_better():
    text = "Can you make it better?"
    result = check_intent(text)
    assert result == BinaryCheck.NO


def test_intent_vague_help_me():
    text = "Help me"
    result = check_intent(text)
    assert result == BinaryCheck.NO


def test_intent_vague_fix_this():
    text = "Fix this"
    result = check_intent(text)
    assert result == BinaryCheck.NO


def test_intent_clear_with_specific_goal():
    text = "Review this code to improve performance"
    result = check_intent(text)
    assert result == BinaryCheck.YES


def test_intent_case_insensitive_detection():
    text = "HELP ME PLEASE"
    result = check_intent(text)
    assert result == BinaryCheck.NO