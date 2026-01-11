import pytest

from orchestrator.orchestrator import ConversationOrchestrator
from orchestrator.models import SessionState

from memory_manager.enums import MemoryQueryResult
from uncertainty_engine.enums import UncertaintyLevel
from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# DUMMY DEPENDENCIES
# ---------------------------------------------------------------------

class DummyMemoryManager:
    write_attempted = False
    confirmation_requested = False
    last_scope = None

    def query_memory(self, user_input: str):
        return MemoryQueryResult.PRESENT

    def render_relevant_memory(self):
        return "Memory context"


class DummyUncertaintyEngine:
    last_context = "ctx"
    last_intent_summary = "intent"
    assumptions_required = False

    def evaluate(self, user_input: str, memory_result):
        return UncertaintyLevel.LEVEL_2  # SAFE → NORMAL / DELIBERATIVE allowed


class DummyPolicyEngine:
    def recommend_mode(self, uncertainty_level):
        return PacingMode.DELIBERATIVE

    def get_forbidden_patterns(self):
        return []

    def get_grounding_questions(self, reason: str):
        return ["Q1", "Q2", "Q3", "Q4", "Q5"]


class DummyPacingLimits:
    target_tokens = 100
    hard_cap_tokens = 200


class ContinueDecision:
    must_continue = True


class StopDecision:
    must_continue = False


class DummyPacingController:
    def __init__(self):
        self.call_count = 0

    def get_limits(self, mode):
        return DummyPacingLimits()

    def build_mode_instruction(self, mode):
        return "DELIBERATIVE instruction"

    def evaluate_output(self, mode, text):
        # First call → continue, second → stop
        self.call_count += 1
        return ContinueDecision() if self.call_count == 1 else StopDecision()


class DummyLLMResult:
    text = "Partial reasoning"
    token_usage_output = 80
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

def test_deliberative_continuation_and_state_increment():
    """
    DELIBERATIVE:
    - First turn → must_continue
    - Structured continuation object returned
    - deliberative_turn_count increments
    """

    session = SessionState(session_id="delib-1")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=DummyLLMExecutor(),
        output_validator=DummyOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    result = orchestrator.handle_turn(session, "Start reasoning")

    assert isinstance(result, dict)
    assert result["type"] == "DELIBERATIVE_CONTINUE"
    assert result["turn_index"] == 1

    assert session.deliberative_turn_count == 1
    assert session.mode == PacingMode.DELIBERATIVE


def test_deliberative_stops_and_resets_counter():
    """
    DELIBERATIVE:
    - Second turn → must_continue = False
    - Raw text returned
    - deliberative_turn_count reset to 0
    """

    session = SessionState(session_id="delib-2")
    session.deliberative_turn_count = 1  # Simulate prior continuation

    pacing = DummyPacingController()
    pacing.call_count = 1  # Force stop decision on first call here

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=pacing,
        llm_executor=DummyLLMExecutor(),
        output_validator=DummyOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    result = orchestrator.handle_turn(session, "Continue reasoning")

    assert isinstance(result, str)
    assert result == "Partial reasoning"

    assert session.deliberative_turn_count == 0