import pytest
from unittest.mock import MagicMock

from llm_executor.executor import LLMExecutor
from llm_executor.models import LLMRequest, LLMResponse
from llm_executor.adapters.base import BaseLLMAdapter
from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# Test adapter (mock)
# ---------------------------------------------------------------------

class MockAdapter(BaseLLMAdapter):
    def __init__(self, response: LLMResponse):
        self.response = response
        self.last_prompt = None
        self.last_max_tokens = None

    def generate(self, prompt: str, max_tokens: int) -> LLMResponse:
        self.last_prompt = prompt
        self.last_max_tokens = max_tokens
        return self.response


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def sample_request():
    return LLMRequest(
        system_instruction="Do the task.",
        user_content="User input here.",
        pacing_mode=PacingMode.NORMAL,
        token_limit=1234,
        forbidden_patterns=["No guessing"],
        claim_label_required=False,
        turn_index=None,
    )


@pytest.fixture
def sample_response():
    return LLMResponse(
        text="Generated output",
        token_usage_input=10,
        token_usage_output=20,
        model_name="test-model",
        raw_provider_response={"id": "abc"},
    )


# ---------------------------------------------------------------------
# Executor tests
# ---------------------------------------------------------------------

def test_executor_calls_adapter_with_correct_max_tokens(sample_request, sample_response):
    adapter = MockAdapter(sample_response)
    executor = LLMExecutor(adapter)

    executor.execute(sample_request)

    assert adapter.last_max_tokens == sample_request.token_limit


def test_executor_passes_prompt_unchanged(sample_request, sample_response):
    adapter = MockAdapter(sample_response)
    executor = LLMExecutor(adapter)

    response = executor.execute(sample_request)

    # The prompt must be built and passed exactly once
    assert adapter.last_prompt is not None
    assert isinstance(adapter.last_prompt, str)
    assert len(adapter.last_prompt) > 0


def test_executor_returns_response_unchanged(sample_request, sample_response):
    adapter = MockAdapter(sample_response)
    executor = LLMExecutor(adapter)

    response = executor.execute(sample_request)

    assert response is sample_response
    assert response.text == "Generated output"
    assert response.token_usage_input == 10
    assert response.token_usage_output == 20
    assert response.model_name == "test-model"
    assert response.raw_provider_response == {"id": "abc"}