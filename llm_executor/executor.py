from llm_executor.models import LLMRequest, LLMResponse
from llm_executor.adapters.base import BaseLLMAdapter
from llm_executor.prompt_builder import build_prompt
from llm_executor.errors import LLMExecutionError


class LLMExecutor:
    """
    Strict execution wrapper around an LLM adapter.

    Responsibilities:
    - Build the final prompt
    - Call the adapter exactly once
    - Return the raw LLMResponse unchanged

    This class does NOT:
    - Validate output
    - Interpret content
    - Retry failures
    - Enforce policy, pacing, or uncertainty
    """

    def __init__(self, adapter: BaseLLMAdapter):
        if adapter is None:
            raise LLMExecutionError("LLMExecutor requires a valid BaseLLMAdapter")

        self.adapter = adapter

    def execute(self, request: LLMRequest) -> LLMResponse:
        """
        Execute a single LLM request.

        Execution flow (non-negotiable):
        1. Build prompt
        2. Call adapter.generate
        3. Return LLMResponse unchanged
        """

        if request is None:
            raise LLMExecutionError("LLMRequest must not be None")

        prompt = build_prompt(request)

        response = self.adapter.generate(
            prompt=prompt,
            max_tokens=request.token_limit,
        )

        return response