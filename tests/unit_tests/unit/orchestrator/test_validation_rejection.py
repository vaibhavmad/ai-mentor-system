import pytest

from orchestrator.orchestrator import ConversationOrchestrator
from orchestrator.models import SessionState

from memory_manager.enums import MemoryQueryResult
from uncertainty_engine.enums import UncertaintyLevel
from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# STRICT DUMMIES — VALIDATOR FORCED TO REJECT
# ---------------------------------------------------------------------

class DummyMemoryManager:
    write_attempted = False
    confirmation_requested = False
    last_scope = None

    def query_memory(self, user_input: str):
        return MemoryQueryResult.PRESENT

    def render_relevant_memory(self):
        return "memory"


class DummyUncertaintyEngine:
    last_context = "context"
    last_intent_summary = "learn python"
    assumptions_required = False

    def evaluate(self, user_input: str, memory_result):
        return UncertaintyLevel.LEVEL_2


class DummyPolicyEngine:
    def recommend_mode(self, uncertainty_level):
        return PacingMode.NORMAL

    def get_forbidden_patterns(self):
        return []

    def get_grounding_questions(self, reason: str):
        return ["Q1", "Q2", "Q3", "Q4", "Q5"]

    def get_intake_questions(self):
        return ["I1", "I2", "I3", "I4", "I5"]

    def get_user_choice_options(self):
        return {"A": "Fast", "B": "Careful", "C": "Deep"}


class DummyPacingLimits:
    target_tokens = 100
    hard_cap_tokens = 200


class DummyPacingDecision:
    must_continue = False


class DummyPacingController:
    def get_limits(self, mode):
        return DummyPacingLimits()

    def build_mode_instruction(self, mode):
        return "instruction"

    def evaluate_output(self, mode, text):
        return DummyPacingDecision()


class DummyLLMResult:
    text = "Invalid answer that violates policy"
    token_usage_output = 50
    raw_provider_response = {}


class DummyLLMExecutor:
    def execute(
        self,
        instruction,
        user_input,
        context_block,
        token_limit,
        mode,
        forbidden_patterns,
        turn_index,
    ):
        return DummyLLMResult()


class RejectingOutputValidator:
    """
    Validator that ALWAYS rejects.
    Used to verify orchestrator behavior on rejection.
    """

    def validate(self, text, context):
        class Result:
            status = "REJECTED"
        return Result()

    def scan_confidence_levels(self, text: str) -> bool:
        return False


# ---------------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------------

def test_validation_rejection_routes_to_grounding():
    """
    If OutputValidator rejects:
    - Orchestrator MUST NOT return ValidationResult
    - Orchestrator MUST route to GROUNDING
    - Reason must be deterministic
    """

    session = SessionState(session_id="reject-1")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=DummyLLMExecutor(),
        output_validator=RejectingOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    result = orchestrator.handle_turn(session, "Explain something risky")

    assert result.type == "GROUNDING"
    assert result.reason == "validation_violation"
    assert isinstance(result.questions, list)
    assert len(result.questions) == 5


def test_validation_rejection_never_returns_text():
    """
    Rejected output must NEVER leak raw LLM text.
    """

    session = SessionState(session_id="reject-2")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=DummyLLMExecutor(),
        output_validator=RejectingOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    result = orchestrator.handle_turn(session, "Another risky request")

    assert not isinstance(result, str)
    assert result.type == "GROUNDING"


def test_validation_rejection_does_not_mutate_session_state():
    """
    Validation rejection must not corrupt session state.
    """

    session = SessionState(session_id="reject-3")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=DummyLLMExecutor(),
        output_validator=RejectingOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    orchestrator.handle_turn(session, "Trigger rejection")

    # Allowed mutations only
    assert session.turn_index == 1
    assert session.mode == PacingMode.NORMAL

    # Forbidden mutations
    assert session.user_choice is None
    assert session.deliberative_turn_count == 0