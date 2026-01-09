import os

from openai import OpenAI

from llm_executor.adapters.base import BaseLLMAdapter
from llm_executor.models import LLMResponse
from llm_executor.errors import ProviderError, LLMExecutionError


class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI adapter using the Responses API.

    Non-negotiable guarantees:
    - Uses Responses API ONLY
    - Hard-forces temperature = 0.0
    - Uses provider-reported token usage ONLY
    - Preserves raw provider response
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-5.2",
        timeout_seconds: int = 30,
        temperature: float | None = None,  # Ignored intentionally
    ):
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise LLMExecutionError("OPENAI_API_KEY is required for OpenAIAdapter")

        self.model = model

        # Client initialization is deterministic and stateless
        self.client = OpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
        )

    def generate(self, prompt: str, max_tokens: int) -> LLMResponse:
        """
        Execute a prompt using OpenAI Responses API.

        HARD RULES:
        - temperature is ALWAYS 0.0
        - token usage MUST be present or fail
        - no retries
        - no estimation
        """

        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                max_output_tokens=max_tokens,
                temperature=0.0,  # HARD-FORCED determinism
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI provider failure: {exc}") from exc

        # Validate provider response shape
        if not hasattr(response, "usage") or response.usage is None:
            raise ProviderError("OpenAI response missing usage information")

        if not hasattr(response.usage, "input_tokens") or not hasattr(
            response.usage, "output_tokens"
        ):
            raise ProviderError("OpenAI usage missing token counts")

        # Extract text output (Responses API canonical accessor)
        try:
            text = response.output_text
        except Exception as exc:
            raise ProviderError("Failed to extract output_text from OpenAI response") from exc

        return LLMResponse(
            text=text,
            token_usage_input=response.usage.input_tokens,
            token_usage_output=response.usage.output_tokens,
            model_name=response.model,
            raw_provider_response=response.to_dict(),
        )