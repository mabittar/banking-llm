from unittest.mock import AsyncMock

import pytest

from src.graph.prompts.identify_intent import IntentResult
from src.services.intent_service import IntentService


@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    service.generate_structured = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_classify_valid_list_keys_intent(mock_llm_service):
    mock_llm_service.generate_structured.return_value = IntentResult(
        intent="list_keys",
        fin_account_id="550e8400-e29b-41d4-a716-446655440000",
        pix_key=None,
    )
    service = IntentService(mock_llm_service)
    messages = [type("Msg", (), {"content": "Quais são as chaves pix ativas da conta 550e8400?"})()]

    result = await service.classify(messages)

    assert result["command"] == "list_keys"
    assert result["fin_account_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert result["pix_key"] is None


@pytest.mark.asyncio
async def test_classify_valid_read_key_intent(mock_llm_service):
    mock_llm_service.generate_structured.return_value = IntentResult(
        intent="read_key",
        fin_account_id="abc-123",
        pix_key="email@test.com",
    )
    service = IntentService(mock_llm_service)
    messages = [type("Msg", (), {"content": "Ver detalhes da chave email@test.com da conta abc-123"})()]

    result = await service.classify(messages)

    assert result["command"] == "read_key"
    assert result["fin_account_id"] == "abc-123"
    assert result["pix_key"] == "email@test.com"


@pytest.mark.asyncio
async def test_classify_unknown_intent_without_account_id(mock_llm_service):
    mock_llm_service.generate_structured.return_value = IntentResult(
        intent="unknown",
        fin_account_id=None,
        pix_key=None,
    )
    service = IntentService(mock_llm_service)
    messages = [type("Msg", (), {"content": "Qual a previsão do tempo?"})()]

    result = await service.classify(messages)

    assert result["command"] == "unknown"


@pytest.mark.asyncio
async def test_classify_handles_empty_messages(mock_llm_service):
    mock_llm_service.generate_structured.return_value = IntentResult(
        intent="unknown",
        fin_account_id=None,
        pix_key=None,
    )
    service = IntentService(mock_llm_service)

    result = await service.classify([])

    assert result["command"] == "unknown"


@pytest.mark.asyncio
async def test_classify_llm_exception_returns_unknown(mock_llm_service):
    mock_llm_service.generate_structured.side_effect = Exception("LLM failure")
    service = IntentService(mock_llm_service)
    messages = [type("Msg", (), {"content": "alguma mensagem"})()]

    result = await service.classify(messages)

    assert result["command"] == "unknown"
    assert "LLM failure" in result["action_error"]
