import pytest
from datetime import datetime

from tests.fixtures.fake_llm import FakeLLM
from tests.fixtures.fake_clock import FakeClock
from tests.fixtures.fake_tokenizer import FakeTokenizer

from policy_engine.policy_engine import PolicyEngine
from memory_manager.manager import MemoryManager
from uncertainty_engine.engine import UncertaintyEngine
from pacing_controller.controller import PacingController
from llm_executor.executor import LLMExecutor
from output_validator.validator import OutputValidator
from orchestrator.orchestrator import ConversationOrchestrator


DEFAULT_DATE = datetime(2024, 1, 1)


@pytest.fixture
def build_system():
    """
    Deterministic system builder.

    Each call returns:
    - a fully wired system
    - fresh state
    - no shared globals
    """

    def _builder(
        *,
        fake_llm_responses,
        policy_path="policy_v1.3.2.yaml",
    ):
        # ------------------------------
        # Policy
        # ------------------------------
        policy_engine = PolicyEngine(policy_path)

        # ------------------------------
        # Fakes
        # ------------------------------
        fake_llm = FakeLLM(fake_llm_responses)
        fake_clock = FakeClock(start_date=DEFAULT_DATE)
        fake_tokenizer = FakeTokenizer()

        # ------------------------------
        # Core Components
        # ------------------------------
        memory_manager = MemoryManager(clock=fake_clock)

        uncertainty_engine = UncertaintyEngine(
            policy_engine=policy_engine
        )

        pacing_controller = PacingController(
            policy_engine=policy_engine
        )

        llm_executor = LLMExecutor(
            adapter=fake_llm,
            tokenizer=fake_tokenizer,
        )

        output_validator = OutputValidator(
            policy_engine=policy_engine
        )

        orchestrator = ConversationOrchestrator(
            memory_manager=memory_manager,
            uncertainty_engine=uncertainty_engine,
            pacing_controller=pacing_controller,
            llm_executor=llm_executor,
            output_validator=output_validator,
            policy_engine=policy_engine,
        )

        return orchestrator

    return _builder