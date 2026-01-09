from abc import ABC, abstractmethod

from llm_executor.models import LLMResponse


class BaseLLMAdapter(ABC):
    """
    Abstract base class for all LLM provider adapters.

    This defines the ONLY contract the LLMExecutor relies on.
    Provider-specific volatility must be isolated behind this interface.
    """

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int) -> LLMResponse:
        """
        Execute a prompt against an LLM provider.

        Args:
            prompt: Fully constructed prompt string (no modification allowed)
            max_tokens: Hard token limit enforced by pacing (must be respected)

        Returns:
            LLMResponse containing:
            - generated text
            - token usage (input + output)
            - model name
            - raw provider response

        Raises:
            ProviderError for any provider-side failure
            LLMExecutionError for internal adapter misuse
        """
        raise NotImplementedError