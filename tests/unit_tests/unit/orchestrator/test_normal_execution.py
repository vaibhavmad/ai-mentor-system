import pytest

from orchestrator.orchestrator import ConversationOrchestrator
from orchestrator.models import SessionState

from memory_manager.enums import MemoryQueryResult
from uncertainty_engine.enums import UncertaintyLevel
from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# DUMMY DEPENDENCIES (STRICT, DETERMINISTIC)
# ---------------------------------------------------------------------

class DummyMemoryManager:
    write_attempted = False
    confirmation_requested = False
    last_scope = None

    def query_memory(self, user_input: str):
        return MemoryQueryResult.PRESENT

    def render_relevant_memory(self):
        return "Relevant memory block"


class DummyUncertaintyEngine:
    last_context = "context"
    last_intent_summary = "user intent"
    assumptions_required = False

    def evaluate(self, user_input: str, memory_result):
        return UncertaintyLevel.LEVEL_2  # SAFE → NORMAL execution


class DummyPolicyEngine:
    def recommend_mode(self, uncertainty_level):
        assert uncertainty_level == UncertaintyLevel.LEVEL_2
        return PacingMode.NORMAL

    def get_forbidden_patterns(self):
        return []

    def get_grounding_questions(self, reason: str):
        return ["Q1", "Q2", "Q3", "Q4", "Q5"]


class DummyPacingLimits:
    target_tokens = 100
    hard_cap_tokens = 200


class DummyPacingDecision:
    must_continue = False


class DummyPacingController:
    def get_limits(self, mode):
        assert mode == PacingMode.NORMAL
        return DummyPacingLimits()

    def build_mode_instruction(self, mode):
        return "NORMAL instruction"

    def evaluate_output(self, mode, text):
        return DummyPacingDecision()


class DummyLLMResult:
    text = "Final answer text"
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
        # Ensure contract compliance
        assert instruction == "NORMAL instruction"
        assert token_limit == 200
        assert mode == PacingMode.NORMAL

        return DummyLLMResult()


class DummyOutputValidator:
    def validate(self, text, context):
        class Result:
            status = "ACCEPTED"
        return Result()

    def scan_confidence_levels(self, text: str) -> bool:
        return False


# ---------------------------------------------------------------------
# NORMAL EXECUTION TEST
# ---------------------------------------------------------------------

def test_normal_execution_returns_raw_text_and_mutates_state():
    """
    LEVEL2 → NORMAL execution
    - Pacing enforced
    - LLM called
    - Validator called
    - Raw text returned
    - State mutated correctly
    """

    session = SessionState(session_id="normal-1")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=DummyLLMExecutor(),
        output_validator=DummyOutputValidator(),
        policy_engine=DummyPolicyEngine(),
    )

    result = orchestrator.handle_turn(
        session=session,
        user_input="Clear question",
    )

    # NORMAL returns RAW TEXT ONLY
    assert isinstance(result, str)
    assert result == "Final answer text"

    # State mutation checks
    assert session.turn_index == 1
    assert session.mode == PacingMode.NORMAL
    assert session.user_choice is None
    assert session.deliberative_turn_count == 0