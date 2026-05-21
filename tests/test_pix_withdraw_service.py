from unittest.mock import AsyncMock, patch

import pytest
from requests import HTTPError, Response

from src.services.pix_withdraw_service import PixWithdrawService


@pytest.fixture
def mock_banking_client():
    client = AsyncMock()
    client.pix_transfer = AsyncMock()
    return client


def _make_http_error(status_code: int) -> HTTPError:
    response = Response()
    response.status_code = status_code
    error = HTTPError(response=response)
    return error


def _base_manual_state() -> dict:
    return {
        "withdraw_amount": 200.0,
        "withdraw_init_type": "MANUAL",
        "withdraw_beneficiary": {
            "holderName": "Test User",
            "governmentId": "12345678901",
            "code": "001",
            "agency": "0001",
            "account": "12345",
            "digit": "6",
            "accountType": "checking",
        },
        "withdraw_end_to_end_id": None,
        "withdraw_additional_info": "test payment",
        "withdraw_qr_code": None,
        "withdraw_reconciliation_id": None,
        "withdraw_key_id": None,
        "withdraw_amount_type": None,
        "withdraw_nominal_amount": None,
    }


def _base_dict_state() -> dict:
    return {
        "withdraw_amount": 1000.0,
        "withdraw_init_type": "DICT",
        "withdraw_beneficiary": {
            "holderName": "Empresa Exemplo",
            "governmentId": "12345678000199",
            "code": "001",
            "agency": "0001",
            "account": "12345",
            "digit": "6",
            "accountType": "checking",
            "pixKey": "contato@empresa.com.br",
        },
        "withdraw_end_to_end_id": "E00000000202600001200AbCdEfGhIjKl",
        "withdraw_additional_info": None,
        "withdraw_qr_code": None,
        "withdraw_reconciliation_id": None,
        "withdraw_key_id": None,
        "withdraw_amount_type": None,
        "withdraw_nominal_amount": None,
    }


def _base_qrcode_state() -> dict:
    return {
        "withdraw_amount": 549.29,
        "withdraw_init_type": "DYNAMIC_QR_CODE",
        "withdraw_beneficiary": {
            "holderName": "Beneficiario",
            "governmentId": "12345678000199",
            "code": "001",
            "agency": "0001",
            "account": "1234567",
            "digit": "0",
            "accountType": "checking",
            "pixKey": "some-uuid-key",
        },
        "withdraw_end_to_end_id": "E00000000202600001200AbCdEfGhIjKl",
        "withdraw_additional_info": None,
        "withdraw_qr_code": "00020126940014br.gov.bcb.pix...",
        "withdraw_reconciliation_id": "6db5125deb834bc59009b3bd25aa323c",
        "withdraw_key_id": "some-uuid-key",
        "withdraw_amount_type": "FIXED",
        "withdraw_nominal_amount": 549.29,
    }


# --- Success cases ---


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_manual_success(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    mock_banking_client.pix_transfer.return_value = type(
        "Resp",
        (),
        {
            "model_dump": lambda self: {
                "uuid": "txn-123",
                "end_to_end_id": None,
                "amount": 200.0,
                "status": "CREATED",
            }
        },
    )()
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(_base_manual_state())

    assert result["action_success"] is True
    assert result["action_data"]["uuid"] == "txn-123"
    mock_banking_client.pix_transfer.assert_awaited_once()
    call_args = mock_banking_client.pix_transfer.call_args
    assert call_args[0][0] == "primary-account"
    assert call_args[0][1]["initType"] == "MANUAL"
    assert call_args[0][1]["amount"] == 200.0


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_dict_success(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    mock_banking_client.pix_transfer.return_value = type(
        "Resp",
        (),
        {
            "model_dump": lambda self: {
                "uuid": "txn-456",
                "end_to_end_id": "E00000000202600001200AbCdEfGhIjKl",
                "amount": 1000.0,
                "status": "CREATED",
            }
        },
    )()
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(_base_dict_state())

    assert result["action_success"] is True
    assert result["action_data"]["uuid"] == "txn-456"
    call_payload = mock_banking_client.pix_transfer.call_args[0][1]
    assert call_payload["initType"] == "DICT"
    assert call_payload["endToEndId"] == "E00000000202600001200AbCdEfGhIjKl"


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_qrcode_success(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    mock_banking_client.pix_transfer.return_value = type(
        "Resp",
        (),
        {
            "model_dump": lambda self: {
                "uuid": "txn-789",
                "end_to_end_id": "E000",
                "amount": 549.29,
                "status": "CREATED",
            }
        },
    )()
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(_base_qrcode_state())

    assert result["action_success"] is True
    call_payload = mock_banking_client.pix_transfer.call_args[0][1]
    assert call_payload["initType"] == "DYNAMIC_QR_CODE"
    assert call_payload["qrCode"] == "00020126940014br.gov.bcb.pix..."
    assert call_payload["reconciliationId"] == "6db5125deb834bc59009b3bd25aa323c"
    assert call_payload["keyId"] == "some-uuid-key"
    assert call_payload["amountType"] == "FIXED"
    assert call_payload["nominalAmount"] == 549.29


# --- Validation error cases ---


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_invalid_amount_zero(mock_settings, mock_banking_client):
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    state = _base_manual_state()
    state["withdraw_amount"] = 0
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "amount" in result["action_error"].lower()
    mock_banking_client.pix_transfer.assert_not_awaited()


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_invalid_amount_negative(mock_settings, mock_banking_client):
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    state = _base_manual_state()
    state["withdraw_amount"] = -50.0
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "amount" in result["action_error"].lower()


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_invalid_amount_too_many_decimals(
    mock_settings, mock_banking_client
):
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    state = _base_manual_state()
    state["withdraw_amount"] = "100.555"
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "2 decimal places" in result["action_error"]
    mock_banking_client.pix_transfer.assert_not_awaited()


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_amount_string_converted_to_decimal(
    mock_settings, mock_banking_client
):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    mock_banking_client.pix_transfer.return_value = type(
        "Resp",
        (),
        {
            "model_dump": lambda self: {
                "uuid": "txn-dec",
                "amount": 99.90,
                "status": "CREATED",
            }
        },
    )()
    state = _base_manual_state()
    state["withdraw_amount"] = "99.90"
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is True
    call_payload = mock_banking_client.pix_transfer.call_args[0][1]
    assert call_payload["amount"] == 99.90


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_dict_without_end_to_end_id(mock_settings, mock_banking_client):
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    state = _base_dict_state()
    state["withdraw_end_to_end_id"] = None
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "end_to_end_id" in result["action_error"]


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_dict_without_pix_key(mock_settings, mock_banking_client):
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    state = _base_dict_state()
    state["withdraw_beneficiary"]["pixKey"] = None
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "pixKey" in result["action_error"]


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_manual_incomplete_beneficiary(
    mock_settings, mock_banking_client
):
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    state = _base_manual_state()
    del state["withdraw_beneficiary"]["code"]
    del state["withdraw_beneficiary"]["agency"]
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "incomplete" in result["action_error"].lower()
    assert "code" in result["action_error"]
    assert "agency" in result["action_error"]


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_missing_transaction_hash_secret(
    mock_settings, mock_banking_client
):
    mock_settings.TRANSACTION_HASH_SECRET = ""
    state = _base_manual_state()
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "secret" in result["action_error"].lower()


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_qrcode_missing_qr_code(mock_settings, mock_banking_client):
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    state = _base_qrcode_state()
    state["withdraw_qr_code"] = None
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "qrCode" in result["action_error"]


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_qrcode_missing_reconciliation_id(
    mock_settings, mock_banking_client
):
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    state = _base_qrcode_state()
    state["withdraw_reconciliation_id"] = None
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(state)

    assert result["action_success"] is False
    assert "reconciliationId" in result["action_error"]


# --- Fallback + API error cases ---


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_fallback_on_retryable_error(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    mock_banking_client.pix_transfer.side_effect = [
        _make_http_error(422),
        type(
            "Resp",
            (),
            {
                "model_dump": lambda self: {
                    "uuid": "txn-fallback",
                    "amount": 200.0,
                    "status": "CREATED",
                }
            },
        )(),
    ]
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(_base_manual_state())

    assert result["action_success"] is True
    assert result["action_data"]["uuid"] == "txn-fallback"
    assert mock_banking_client.pix_transfer.await_count == 2


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_no_fallback_on_non_retryable_error(
    mock_settings, mock_banking_client
):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    mock_banking_client.pix_transfer.side_effect = _make_http_error(400)
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(_base_manual_state())

    assert result["action_success"] is False
    mock_banking_client.pix_transfer.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.services.pix_withdraw_service.settings")
async def test_execute_fin_account_not_configured(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = ""
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_settings.TRANSACTION_HASH_SECRET = "test-secret"
    service = PixWithdrawService(mock_banking_client)

    result = await service.execute(_base_manual_state())

    assert result["action_success"] is False
    assert "FIN_ACCOUNT_ID" in result["action_error"]
