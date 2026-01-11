import pytest

from orchestrator.orchestrator import ConversationOrchestrator
from orchestrator.models import SessionState

from memory_manager.enums import MemoryQueryResult
from uncertainty_engine.enums import UncertaintyLevel
from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# DUMMY DEPENDENCIES (STRICT, NO SIDE EFFECTS)
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
    last_context = "learning-context"
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
    text = "Final answer"
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


class DummyOutputValidator:
    def validate(self, text, context):
        class Result:
            status = "ACCEPTED"
        return Result()

    def scan_confidence_levels(self, text: str) -> bool:
        return False


# ---------------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------------

def test_only_allowed_state_fields_mutate():
    """
    Ensures that only explicitly allowed SessionState fields mutate.
    """

    session = SessionState(session_id="state-1")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=DummyLLMExecutor(),
        output_validator=DummyOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    # Snapshot initial state
    initial_state = session.__dict__.copy()

    result = orchestrator.handle_turn(session, "Explain Python")

    # Allowed mutations
    assert session.turn_index == initial_state["turn_index"] + 1
    assert session.active_context == "learning-context"
    assert session.mode == PacingMode.NORMAL

    # Forbidden mutations (must remain unchanged)
    assert session.user_choice is None
    assert session.deliberative_turn_count == 0

    # Session ID must NEVER change
    assert session.session_id == initial_state["session_id"]


def test_no_state_leak_between_turns():
    """
    Ensures state does not leak incorrectly across turns.
    """

    session = SessionState(session_id="state-2")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=DummyLLMExecutor(),
        output_validator=DummyOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    # Turn 1
    orchestrator.handle_turn(session, "First input")

    assert session.turn_index == 1
    assert session.mode == PacingMode.NORMAL
    assert session.user_choice is None

    # Turn 2
    orchestrator.handle_turn(session, "Second input")

    assert session.turn_index == 2
    assert session.mode == PacingMode.NORMAL
    assert session.user_choice is None


def test_user_choice_does_not_set_mode_early():
    """
    USER_CHOICE route must not mutate mode or user_choice prematurely.
    """

    class Level3UncertaintyEngine(DummyUncertaintyEngine):
        def evaluate(self, user_input, memory_result):
            return UncertaintyLevel.LEVEL_3

    session = SessionState(session_id="state-3")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=Level3UncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=DummyLLMExecutor(),
        output_validator=DummyOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    result = orchestrator.handle_turn(session, "Ambiguous request")

    assert result.type == "USER_CHOICE"

    # No mutation allowed yet
    assert session.user_choice is None
    assert session.mode is None
    assert session.deliberative_turn_count == 0