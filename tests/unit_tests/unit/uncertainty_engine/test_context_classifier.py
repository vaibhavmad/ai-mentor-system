import pytest

from uncertainty_engine.context_classifier import classify_context
from uncertainty_engine.enums import Context
from uncertainty_engine.errors import AmbiguousContextError


# -------------------------
# Single-context detection
# -------------------------

def test_learning_context_detected():
    text = "I want to learn Python basics"
    assert classify_context(text) == Context.LEARNING


def test_code_review_context_detected_with_code_block():
    text = """
    Please review this code:

    ```python
    def add(a, b):
        return a + b
    ```
    """
    assert classify_context(text) == Context.CODE_REVIEW


def test_architecture_design_context_detected():
    text = "Design the architecture for a scalable payment system"
    assert classify_context(text) == Context.ARCHITECTURE_DESIGN


def test_problem_solving_context_detected():
    text = "I am getting a runtime error and need to fix this bug"
    assert classify_context(text) == Context.PROBLEM_SOLVING


def test_decision_making_context_detected():
    text = "Help me decide between PostgreSQL and MySQL based on scalability"
    assert classify_context(text) == Context.DECISION_MAKING


def test_planning_context_detected():
    text = "Create a roadmap to launch this product in three months"
    assert classify_context(text) == Context.PLANNING


def test_evaluation_context_detected():
    text = "Evaluate the quality of this API design"
    assert classify_context(text) == Context.EVALUATION


# -----------------------------------
# Priority & special resolution rules
# -----------------------------------

def test_code_review_wins_over_learning_when_code_present():
    text = """
    I want to learn how to improve this code:

    ```python
    x = 1 + 2
    ```
    """
    assert classify_context(text) == Context.CODE_REVIEW


def test_learning_selected_when_learn_keyword_and_no_code():
    text = "I want to learn system design concepts"
    assert classify_context(text) == Context.LEARNING


# -------------------------
# Ambiguity hard failures
# -------------------------

def test_ambiguous_context_raises_error():
    text = "Design and evaluate the system architecture"
    with pytest.raises(AmbiguousContextError):
        classify_context(text)


# -------------------------
# Default behavior
# -------------------------

def test_default_context_is_learning_when_no_signals():
    text = "Tell me more"
    assert classify_context(text) == Context.LEARNING