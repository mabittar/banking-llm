from unittest.mock import AsyncMock, patch

import pytest
from requests import HTTPError, Response

from src.services.pix_key_service import PixKeyService


@pytest.fixture
def mock_banking_client():
    client = AsyncMock()
    client.list_active_pix_keys = AsyncMock()
    client.read_pix_key = AsyncMock()
    return client


def _make_http_error(status_code: int) -> HTTPError:
    response = Response()
    response.status_code = status_code
    error = HTTPError(response=response)
    return error


@pytest.mark.asyncio
@patch("src.services.pix_key_service.settings")
async def test_list_keys_success_with_primary_account(
    mock_settings, mock_banking_client
):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_banking_client.list_active_pix_keys.return_value = type(
        "Resp", (), {"model_dump": lambda self: {"count": 2, "results": []}}
    )()
    service = PixKeyService(mock_banking_client)

    result = await service.list_keys()

    assert result["action_success"] is True
    assert result["action_data"]["count"] == 2
    mock_banking_client.list_active_pix_keys.assert_awaited_once_with("primary-account")


@pytest.mark.asyncio
@patch("src.services.pix_key_service.settings")
async def test_list_keys_fallback_on_retryable_error(
    mock_settings, mock_banking_client
):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_banking_client.list_active_pix_keys.side_effect = [
        _make_http_error(404),
        type("Resp", (), {"model_dump": lambda self: {"count": 1, "results": []}})(),
    ]
    service = PixKeyService(mock_banking_client)

    result = await service.list_keys()

    assert result["action_success"] is True
    assert result["action_data"]["count"] == 1
    assert mock_banking_client.list_active_pix_keys.await_count == 2


@pytest.mark.asyncio
@patch("src.services.pix_key_service.settings")
async def test_list_keys_both_accounts_fail(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_banking_client.list_active_pix_keys.side_effect = [
        _make_http_error(404),
        _make_http_error(404),
    ]
    service = PixKeyService(mock_banking_client)

    result = await service.list_keys()

    assert result["action_success"] is False
    assert result["action_error"] is not None


@pytest.mark.asyncio
@patch("src.services.pix_key_service.settings")
async def test_list_keys_no_fallback_on_non_retryable_error(
    mock_settings, mock_banking_client
):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_banking_client.list_active_pix_keys.side_effect = Exception(
        "Connection timeout"
    )
    service = PixKeyService(mock_banking_client)

    result = await service.list_keys()

    assert result["action_success"] is False
    assert "Connection timeout" in result["action_error"]
    mock_banking_client.list_active_pix_keys.assert_awaited_once_with("primary-account")


@pytest.mark.asyncio
@patch("src.services.pix_key_service.settings")
async def test_list_keys_fin_account_not_configured(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = ""
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    service = PixKeyService(mock_banking_client)

    result = await service.list_keys()

    assert result["action_success"] is False
    assert "not configured" in result["action_error"]
    mock_banking_client.list_active_pix_keys.assert_not_called()


@pytest.mark.asyncio
@patch("src.services.pix_key_service.settings")
async def test_read_key_success_with_primary_account(
    mock_settings, mock_banking_client
):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_banking_client.read_pix_key.return_value = type(
        "Resp", (), {"model_dump": lambda self: {"end_to_end_id": "E2E123"}}
    )()
    service = PixKeyService(mock_banking_client)

    result = await service.read_key("email@test.com")

    assert result["action_success"] is True
    assert result["action_data"]["end_to_end_id"] == "E2E123"
    mock_banking_client.read_pix_key.assert_awaited_once_with(
        "email@test.com", "primary-account"
    )


@pytest.mark.asyncio
@patch("src.services.pix_key_service.settings")
async def test_read_key_fallback_on_retryable_error(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_banking_client.read_pix_key.side_effect = [
        _make_http_error(422),
        type("Resp", (), {"model_dump": lambda self: {"end_to_end_id": "E2E456"}})(),
    ]
    service = PixKeyService(mock_banking_client)

    result = await service.read_key("email@test.com")

    assert result["action_success"] is True
    assert result["action_data"]["end_to_end_id"] == "E2E456"
    assert mock_banking_client.read_pix_key.await_count == 2


@pytest.mark.asyncio
async def test_read_key_missing_pix_key(mock_banking_client):
    service = PixKeyService(mock_banking_client)

    result = await service.read_key(None)

    assert result["action_success"] is False
    assert "pix_key is required" in result["action_error"]
    mock_banking_client.read_pix_key.assert_not_called()


@pytest.mark.asyncio
@patch("src.services.pix_key_service.settings")
async def test_read_key_no_fallback_without_fallback_configured(
    mock_settings, mock_banking_client
):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_banking_client.read_pix_key.side_effect = _make_http_error(404)
    service = PixKeyService(mock_banking_client)

    result = await service.read_key("key-123")

    assert result["action_success"] is False
    mock_banking_client.read_pix_key.assert_awaited_once()
