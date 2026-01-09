from uncertainty_engine.completeness_checker import check_completeness
from uncertainty_engine.enums import Context, BinaryCheck


# ---------- LEARNING ----------

def test_learning_complete():
    text = "I want to learn Python at a deep level"
    result = check_completeness(Context.LEARNING, text)
    assert result == BinaryCheck.YES


def test_learning_missing_goal():
    text = "I want to learn Python"
    result = check_completeness(Context.LEARNING, text)
    assert result == BinaryCheck.NO


# ---------- CODE REVIEW ----------

def test_code_review_complete():
    text = """
    Please review this code and suggest improvements:

    ```python
    def add(a, b):
        return a + b
    ```
    """
    result = check_completeness(Context.CODE_REVIEW, text)
    assert result == BinaryCheck.YES


def test_code_review_missing_code():
    text = "Please review this and optimize it"
    result = check_completeness(Context.CODE_REVIEW, text)
    assert result == BinaryCheck.NO


# ---------- ARCHITECTURE DESIGN ----------

def test_architecture_design_complete():
    text = "Design a payment system to handle high traffic"
    result = check_completeness(Context.ARCHITECTURE_DESIGN, text)
    assert result == BinaryCheck.YES


def test_architecture_design_missing_goal():
    text = "Design a payment system"
    result = check_completeness(Context.ARCHITECTURE_DESIGN, text)
    assert result == BinaryCheck.NO


# ---------- PROBLEM SOLVING ----------

def test_problem_solving_complete():
    text = "I am getting a runtime error when running my script"
    result = check_completeness(Context.PROBLEM_SOLVING, text)
    assert result == BinaryCheck.YES


def test_problem_solving_missing_problem():
    text = "Something is wrong"
    result = check_completeness(Context.PROBLEM_SOLVING, text)
    assert result == BinaryCheck.NO


# ---------- DECISION MAKING ----------

def test_decision_making_complete():
    text = "Choose a database based on performance and scalability constraints"
    result = check_completeness(Context.DECISION_MAKING, text)
    assert result == BinaryCheck.YES


def test_decision_making_missing_constraints():
    text = "Choose a database based on performance"
    result = check_completeness(Context.DECISION_MAKING, text)
    assert result == BinaryCheck.NO


# ---------- PLANNING ----------

def test_planning_complete():
    text = "Plan a product launch in the next three months"
    result = check_completeness(Context.PLANNING, text)
    assert result == BinaryCheck.YES


def test_planning_missing_time():
    text = "Plan a product launch"
    result = check_completeness(Context.PLANNING, text)
    assert result == BinaryCheck.NO


# ---------- EVALUATION ----------

def test_evaluation_complete():
    text = "Evaluate this framework based on performance and quality"
    result = check_completeness(Context.EVALUATION, text)
    assert result == BinaryCheck.YES


def test_evaluation_missing_standard():
    text = "Evaluate this framework"
    result = check_completeness(Context.EVALUATION, text)
    assert result == BinaryCheck.NO