from typing import List

import pytest
from llm_executor.models import LLMResponse


class FakeLLM:
    """
    Fake LLM that mimics the public behavior of the real LLM adapter.

    HARD RULES:
    - Implements ONLY the public execute() interface
    - Returns real LLMResponse objects
    - No test-only helpers
    - No inspection shortcuts
    """

    def __init__(self, scripted_responses: List[LLMResponse]):
        """
        scripted_responses: List[LLMResponse]
        """
        self._responses = list(scripted_responses)
        self._calls = []

    def execute(self, prompt: str, max_tokens: int) -> LLMResponse:
        """
        Public API identical to production usage.
        """

        self._calls.append(
            {
                "prompt": prompt,
                "max_tokens": max_tokens,
            }
        )

        if not self._responses:
            pytest.fail(
                "FakeLLM exhausted scripted responses — "
                "test did not anticipate number of LLM calls"
            )

        response = self._responses.pop(0)

        if not isinstance(response, LLMResponse):
            pytest.fail(
                "FakeLLM must return LLMResponse instances only"
            )

        return response