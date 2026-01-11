import pytest

from orchestrator.orchestrator import ConversationOrchestrator
from orchestrator.models import SessionState, UserChoicePrompt

from memory_manager.enums import MemoryQueryResult
from uncertainty_engine.enums import UncertaintyLevel
from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# TEST SETUP HELPERS
# ---------------------------------------------------------------------

class DummyMemoryManager:
    def query_memory(self, user_input: str):
        return MemoryQueryResult.PRESENT


class DummyUncertaintyEngine:
    def __init__(self):
        self.last_context = "dummy_context"
        self.last_intent_summary = "ambiguous intent"
        self.assumptions_required = False

    def evaluate(self, user_input: str, memory_result):
        return UncertaintyLevel.LEVEL_3  # forces USER_CHOICE


class DummyPolicyEngine:
    def get_user_choice_options(self):
        return {
            "A": "Fast concise answer",
            "B": "Careful detailed answer",
            "C": "Step-by-step reasoning",
        }

    def recommend_mode(self, uncertainty_level):
        # Should NEVER be used for LEVEL_3
        raise AssertionError("Policy mode recommendation must not run for USER_CHOICE")


class DummyPacingController:
    def map_choice_to_mode(self, choice: str):
        return {
            "A": PacingMode.NORMAL,
            "B": PacingMode.CAREFUL,
            "C": PacingMode.DELIBERATIVE,
        }[choice]


# ---------------------------------------------------------------------
# USER CHOICE FLOW TESTS
# ---------------------------------------------------------------------

def test_user_choice_turn_1_returns_prompt_only():
    """
    Turn 1:
    - USER_CHOICE returns presentation object
    - NO state mutation
    """

    session = SessionState(session_id="uc1")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=None,
        output_validator=None,
        policy_engine=DummyPolicyEngine(),
    )

    response = orchestrator.handle_turn(
        session=session,
        user_input="ambiguous question",
    )

    # Must return structured UserChoicePrompt
    assert isinstance(response, UserChoicePrompt)
    assert response.type == "USER_CHOICE"
    assert set(response.options.keys()) == {"A", "B", "C"}

    # NO mutation allowed in turn 1
    assert session.user_choice is None
    assert session.mode is None


def test_user_choice_turn_2_sets_choice_and_mode():
    """
    Turn 2:
    - User selects A/B/C
    - Orchestrator mutates state
    - Continues to NORMAL execution
    """

    session = SessionState(session_id="uc2")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=None,          # Not exercised in this test
        output_validator=None,      # Not exercised in this test
        policy_engine=DummyPolicyEngine(),
    )

    # ---- TURN 1: present choices ----
    response = orchestrator.handle_turn(
        session=session,
        user_input="ambiguous question",
    )

    assert isinstance(response, UserChoicePrompt)

    # ---- TURN 2: user selects choice ----
    session.user_choice = "C"  # simulated user input
    session.mode = orchestrator.pacing_controller.map_choice_to_mode("C")

    # Validate state mutation
    assert session.user_choice == "C"
    assert session.mode == PacingMode.DELIBERATIVE


def test_user_choice_overrides_policy_recommendation():
    """
    USER_CHOICE must override policy-driven mode selection.
    """

    session = SessionState(session_id="uc3")

    orchestrator = ConversationOrchestrator(
        memory_manager=DummyMemoryManager(),
        uncertainty_engine=DummyUncertaintyEngine(),
        pacing_controller=DummyPacingController(),
        llm_executor=None,
        output_validator=None,
        policy_engine=DummyPolicyEngine(),
    )

    # Turn 1
    response = orchestrator.handle_turn(
        session=session,
        user_input="ambiguous question",
    )

    assert response.type == "USER_CHOICE"

    # Policy engine must NOT set mode
    assert session.mode is None