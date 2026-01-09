from enum import Enum


class Context(Enum):
    LEARNING = "learning"
    CODE_REVIEW = "code_review"
    ARCHITECTURE_DESIGN = "architecture_design"
    PROBLEM_SOLVING = "problem_solving"
    DECISION_MAKING = "decision_making"
    PLANNING = "planning"
    EVALUATION = "evaluation"


class BinaryCheck(Enum):
    YES = "YES"
    NO = "NO"


class UncertaintyLevel(Enum):
    LEVEL_1_2 = "LEVEL_1_2"   # May proceed
    LEVEL_3 = "LEVEL_3"       # Must ask 1–2 clarifying questions
    LEVEL_4 = "LEVEL_4"       # Must ask grounding questions
    LEVEL_5 = "LEVEL_5"       # Blocked until clarified