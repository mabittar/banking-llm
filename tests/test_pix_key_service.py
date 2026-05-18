from unittest.mock import AsyncMock

import pytest

from src.services.pix_key_service import PixKeyService


@pytest.fixture
def mock_banking_client():
    client = AsyncMock()
    client.list_active_pix_keys = AsyncMock()
    client.read_pix_key = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_list_keys_with_valid_id(mock_banking_client):
    mock_banking_client.list_active_pix_keys.return_value = type(
        "Resp",
        (),
        {"model_dump": lambda self: {"count": 2, "results": []}},
    )()
    service = PixKeyService(mock_banking_client)

    result = await service.list_keys("account-123")

    assert result["action_success"] is True
    assert result["action_data"]["count"] == 2
    mock_banking_client.list_active_pix_keys.assert_awaited_once_with("account-123")


@pytest.mark.asyncio
async def test_list_keys_with_none_id(mock_banking_client):
    service = PixKeyService(mock_banking_client)

    result = await service.list_keys(None)

    assert result["action_success"] is False
    assert "required" in result["action_error"]
    mock_banking_client.list_active_pix_keys.assert_not_called()


@pytest.mark.asyncio
async def test_read_key_with_valid_params(mock_banking_client):
    mock_banking_client.read_pix_key.return_value = type(
        "Resp",
        (),
        {
            "model_dump": lambda self: {
                "end_to_end_id": "E2E123",
                "beneficiary": {"holderName": "Joao"},
            }
        },
    )()
    service = PixKeyService(mock_banking_client)

    result = await service.read_key("account-123", "email@test.com")

    assert result["action_success"] is True
    assert result["action_data"]["end_to_end_id"] == "E2E123"
    mock_banking_client.read_pix_key.assert_awaited_once_with("email@test.com", "account-123")


@pytest.mark.asyncio
async def test_read_key_with_missing_param(mock_banking_client):
    service = PixKeyService(mock_banking_client)

    result = await service.read_key(None, "key-123")

    assert result["action_success"] is False
    assert "required" in result["action_error"]
    mock_banking_client.read_pix_key.assert_not_called()


@pytest.mark.asyncio
async def test_read_key_with_none_pix_key(mock_banking_client):
    service = PixKeyService(mock_banking_client)

    result = await service.read_key("account-123", None)

    assert result["action_success"] is False
    assert "required" in result["action_error"]
    mock_banking_client.read_pix_key.assert_not_called()


@pytest.mark.asyncio
async def test_list_keys_api_exception(mock_banking_client):
    mock_banking_client.list_active_pix_keys.side_effect = Exception("API timeout")
    service = PixKeyService(mock_banking_client)

    result = await service.list_keys("account-123")

    assert result["action_success"] is False
    assert "API timeout" in result["action_error"]


@pytest.mark.asyncio
async def test_read_key_api_exception(mock_banking_client):
    mock_banking_client.read_pix_key.side_effect = Exception("API timeout")
    service = PixKeyService(mock_banking_client)

    result = await service.read_key("account-123", "key-123")

    assert result["action_success"] is False
    assert "API timeout" in result["action_error"]
