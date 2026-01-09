import pytest
from dataclasses import FrozenInstanceError

from llm_executor.models import LLMRequest, LLMResponse
from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# LLMRequest tests
# ---------------------------------------------------------------------

def test_llm_request_is_frozen():
    request = LLMRequest(
        system_instruction="Do X",
        user_content="Hello",
        pacing_mode=PacingMode.NORMAL,
        token_limit=100,
        forbidden_patterns=["No guessing"],
        claim_label_required=True,
        turn_index=None,
    )

    with pytest.raises(FrozenInstanceError):
        request.token_limit = 200


def test_llm_request_has_all_required_fields():
    request = LLMRequest(
        system_instruction="Instruction",
        user_content="User text",
        pacing_mode=PacingMode.CAREFUL,
        token_limit=500,
        forbidden_patterns=[],
        claim_label_required=False,
        turn_index=None,
    )

    assert request.system_instruction == "Instruction"
    assert request.user_content == "User text"
    assert request.pacing_mode == PacingMode.CAREFUL
    assert request.token_limit == 500
    assert request.forbidden_patterns == []
    assert request.claim_label_required is False
    assert request.turn_index is None


# ---------------------------------------------------------------------
# LLMResponse tests
# ---------------------------------------------------------------------

def test_llm_response_is_frozen():
    response = LLMResponse(
        text="Output",
        token_usage_input=10,
        token_usage_output=20,
        model_name="test-model",
        raw_provider_response={"id": "123"},
    )

    with pytest.raises(FrozenInstanceError):
        response.text = "Modified"


def test_llm_response_has_all_required_fields():
    raw = {"some": "response"}

    response = LLMResponse(
        text="Generated text",
        token_usage_input=15,
        token_usage_output=25,
        model_name="model-x",
        raw_provider_response=raw,
    )

    assert response.text == "Generated text"
    assert response.token_usage_input == 15
    assert response.token_usage_output == 25
    assert response.model_name == "model-x"
    assert response.raw_provider_response == raw