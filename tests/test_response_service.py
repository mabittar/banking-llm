from unittest.mock import AsyncMock

import pytest

from src.graph.prompts.chat_response import MessageResult
from src.graph.state import GraphState
from src.services.response_service import ResponseService


@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    service.generate_structured = AsyncMock()
    return service


def _state(**overrides) -> GraphState:
    defaults = {
        "messages": [],
        "output": "",
        "command": "unknown",
        "fin_account_id": None,
        "pix_key": None,
        "action_success": None,
        "action_error": None,
        "action_data": None,
    }
    defaults.update(overrides)
    return defaults


@pytest.mark.asyncio
async def test_generate_list_keys_success(mock_llm_service):
    mock_llm_service.generate_structured.return_value = MessageResult(
        message="Aqui estão suas chaves PIX ativas."
    )
    service = ResponseService(mock_llm_service)

    state = _state(command="list_keys", action_success=True, action_data={"count": 2, "results": []})
    result = await service.generate(state)

    assert len(result["messages"]) == 1
    assert "chaves PIX ativas" in result["messages"][0].content


@pytest.mark.asyncio
async def test_generate_list_keys_error(mock_llm_service):
    mock_llm_service.generate_structured.return_value = MessageResult(
        message="Desculpe, ocorreu um erro ao listar as chaves."
    )
    service = ResponseService(mock_llm_service)

    state = _state(command="list_keys", action_success=False, action_error="API failure")
    result = await service.generate(state)

    assert len(result["messages"]) == 1
    assert "erro" in result["messages"][0].content


@pytest.mark.asyncio
async def test_generate_read_key_success(mock_llm_service):
    mock_llm_service.generate_structured.return_value = MessageResult(
        message="Detalhes da chave PIX: email@test.com"
    )
    service = ResponseService(mock_llm_service)

    state = _state(command="read_key", action_success=True, fin_account_id="acc-1", pix_key="email@test.com")
    result = await service.generate(state)

    assert len(result["messages"]) == 1
    assert "email@test.com" in result["messages"][0].content


@pytest.mark.asyncio
async def test_generate_unknown_intent(mock_llm_service):
    mock_llm_service.generate_structured.return_value = MessageResult(
        message="Posso ajudar você com consultas de chaves PIX."
    )
    service = ResponseService(mock_llm_service)

    state = _state(command="unknown")
    result = await service.generate(state)

    assert len(result["messages"]) == 1
    assert "ajudar" in result["messages"][0].content


@pytest.mark.asyncio
async def test_generate_llm_exception_returns_fallback(mock_llm_service):
    mock_llm_service.generate_structured.side_effect = Exception("LLM failure")
    service = ResponseService(mock_llm_service)

    state = _state(command="list_keys", action_success=True)
    result = await service.generate(state)

    assert len(result["messages"]) == 1
    assert "Desculpe" in result["messages"][0].content
    assert "erro" in result["messages"][0].content
