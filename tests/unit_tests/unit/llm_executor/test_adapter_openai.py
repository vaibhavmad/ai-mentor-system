import pytest
from unittest.mock import MagicMock, patch

from llm_executor.adapters.openai import OpenAIAdapter
from llm_executor.errors import ProviderError, LLMExecutionError
from llm_executor.models import LLMResponse


# ---------------------------------------------------------------------
# Helpers to mock OpenAI Responses API objects
# ---------------------------------------------------------------------

class MockUsage:
    def __init__(self, input_tokens=None, output_tokens=None):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockResponse:
    def __init__(
        self,
        text="hello",
        input_tokens=5,
        output_tokens=7,
        model="gpt-4o-mini",
        include_usage=True,
    ):
        self.model = model
        self.output_text = text
        self.usage = (
            MockUsage(input_tokens, output_tokens) if include_usage else None
        )

    def to_dict(self):
        return {
            "model": self.model,
            "output_text": self.output_text,
            "usage": None if self.usage is None else {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
            },
        }


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def adapter():
    # Patch OpenAI client creation so no real API is called
    with patch("llm_executor.adapters.openai.OpenAI") as mock_client:
        instance = mock_client.return_value
        yield OpenAIAdapter(api_key="test-key", model="gpt-4o-mini")


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_responses_api_is_used_and_raw_response_preserved(adapter):
    """
    Verifies:
    - Responses API is called
    - Raw provider response is preserved verbatim
    """

    mock_response = MockResponse()

    adapter.client.responses.create = MagicMock(return_value=mock_response)

    result = adapter.generate(prompt="test prompt", max_tokens=100)

    assert isinstance(result, LLMResponse)
    assert result.text == "hello"
    assert result.token_usage_input == 5
    assert result.token_usage_output == 7
    assert result.model_name == "gpt-4o-mini"
    assert result.raw_provider_response == mock_response.to_dict()

    adapter.client.responses.create.assert_called_once()


def test_missing_usage_raises_provider_error(adapter):
    """
    If provider response is missing usage,
    ProviderError MUST be raised.
    """

    mock_response = MockResponse(include_usage=False)

    adapter.client.responses.create = MagicMock(return_value=mock_response)

    with pytest.raises(ProviderError):
        adapter.generate(prompt="test prompt", max_tokens=100)


def test_missing_token_counts_raises_provider_error(adapter):
    """
    If usage exists but token counts are missing,
    ProviderError MUST be raised.
    """

    bad_response = MockResponse()
    bad_response.usage.input_tokens = None
    bad_response.usage.output_tokens = None

    adapter.client.responses.create = MagicMock(return_value=bad_response)

    with pytest.raises(ProviderError):
        adapter.generate(prompt="test prompt", max_tokens=100)


def test_temperature_is_hard_forced_to_zero(adapter):
    """
    Temperature MUST always be forced to 0.0,
    regardless of any external input.
    """

    mock_response = MockResponse()

    adapter.client.responses.create = MagicMock(return_value=mock_response)

    adapter.generate(prompt="test prompt", max_tokens=100)

    _, kwargs = adapter.client.responses.create.call_args
    assert kwargs["temperature"] == 0.0


def test_provider_exception_is_wrapped_as_provider_error(adapter):
    """
    Any provider / SDK exception MUST raise ProviderError.
    """

    adapter.client.responses.create = MagicMock(
        side_effect=Exception("network failure")
    )

    with pytest.raises(ProviderError):
        adapter.generate(prompt="test prompt", max_tokens=100)