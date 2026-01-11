import pytest

from orchestrator.orchestrator import ConversationOrchestrator
from orchestrator.models import SessionState

from memory_manager.enums import MemoryQueryResult
from uncertainty_engine.enums import UncertaintyLevel


# ---------------------------------------------------------------------
# TEST SETUP HELPERS
# ---------------------------------------------------------------------

class DummyMemoryManager:
    def __init__(self, result):
        self._result = result

    def query_memory(self, user_input: str):
        return self._result


class DummyUncertaintyEngine:
    def __init__(self, level):
        self._level = level
        self.last_context = "dummy_context"

    def evaluate(self, user_input: str, memory_result):
        return self._level


def build_orchestrator(memory_result, uncertainty_level):
    """
    Build an orchestrator with controlled memory + uncertainty outputs.
    """
    memory_manager = DummyMemoryManager(memory_result)
    uncertainty_engine = DummyUncertaintyEngine(uncertainty_level)

    # Downstream dependencies are NOT used in routing tests
    return ConversationOrchestrator(
        memory_manager=memory_manager,
        uncertainty_engine=uncertainty_engine,
        pacing_controller=None,
        llm_executor=None,
        output_validator=None,
        policy_engine=None,
    )


# ---------------------------------------------------------------------
# ROUTING TESTS (LOCKED BEHAVIOR)
# ---------------------------------------------------------------------

def test_empty_memory_routes_to_intake():
    session = SessionState(session_id="s1")

    orchestrator = build_orchestrator(
        memory_result=MemoryQueryResult.EMPTY,
        uncertainty_level=None,
    )

    memory_result, uncertainty = orchestrator.pre_route(
        session,
        user_input="hello",
    )

    route = orchestrator.decide_route(memory_result, uncertainty)

    assert route == "INTAKE"


def test_memory_conflict_always_routes_to_grounding():
    session = SessionState(session_id="s2")

    orchestrator = build_orchestrator(
        memory_result=MemoryQueryResult.CONFLICT,
        uncertainty_level=UncertaintyLevel.LEVEL_1,  # should be ignored
    )

    memory_result, uncertainty = orchestrator.pre_route(
        session,
        user_input="conflicting input",
    )

    route = orchestrator.decide_route(memory_result, uncertainty)

    assert route == "GROUNDING"


def test_high_uncertainty_routes_to_grounding():
    session = SessionState(session_id="s3")

    orchestrator = build_orchestrator(
        memory_result=MemoryQueryResult.PRESENT,
        uncertainty_level=UncertaintyLevel.LEVEL_5,
    )

    memory_result, uncertainty = orchestrator.pre_route(
        session,
        user_input="ambiguous input",
    )

    route = orchestrator.decide_route(memory_result, uncertainty)

    assert route == "GROUNDING"


def test_level_3_uncertainty_routes_to_user_choice():
    session = SessionState(session_id="s4")

    orchestrator = build_orchestrator(
        memory_result=MemoryQueryResult.PRESENT,
        uncertainty_level=UncertaintyLevel.LEVEL_3,
    )

    memory_result, uncertainty = orchestrator.pre_route(
        session,
        user_input="needs clarification",
    )

    route = orchestrator.decide_route(memory_result, uncertainty)

    assert route == "USER_CHOICE"


def test_low_uncertainty_routes_to_normal_execution():
    session = SessionState(session_id="s5")

    orchestrator = build_orchestrator(
        memory_result=MemoryQueryResult.PRESENT,
        uncertainty_level=UncertaintyLevel.LEVEL_2,
    )

    memory_result, uncertainty = orchestrator.pre_route(
        session,
        user_input="clear intent",
    )

    route = orchestrator.decide_route(memory_result, uncertainty)

    assert route == "NORMAL"


# ---------------------------------------------------------------------
# PRECEDENCE GUARANTEE TESTS
# ---------------------------------------------------------------------

def test_conflict_beats_high_uncertainty():
    """
    Even if uncertainty is LEVEL5, memory CONFLICT must win.
    """
    session = SessionState(session_id="s6")

    orchestrator = build_orchestrator(
        memory_result=MemoryQueryResult.CONFLICT,
        uncertainty_level=UncertaintyLevel.LEVEL_5,
    )

    memory_result, uncertainty = orchestrator.pre_route(
        session,
        user_input="conflicting and ambiguous",
    )

    route = orchestrator.decide_route(memory_result, uncertainty)

    assert route == "GROUNDING"


def test_level_3_never_falls_through_to_normal():
    session = SessionState(session_id="s7")

    orchestrator = build_orchestrator(
        memory_result=MemoryQueryResult.PRESENT,
        uncertainty_level=UncertaintyLevel.LEVEL_3,
    )

    memory_result, uncertainty = orchestrator.pre_route(
        session,
        user_input="ambiguous choice",
    )

    route = orchestrator.decide_route(memory_result, uncertainty)

    assert route != "NORMAL"
    assert route == "USER_CHOICE"