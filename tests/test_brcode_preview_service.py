from unittest.mock import AsyncMock, patch

import pytest
from requests import HTTPError, Response

from src.services.brcode_preview_service import BRCodePreviewService


@pytest.fixture
def mock_banking_client():
    client = AsyncMock()
    client.brcode_preview = AsyncMock()
    return client


def _valid_brcode() -> str:
    return (
        "00020126580014br.gov.bcb.pix0136a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        "520400005303986540510.005802BR5913Test Merchant6008Brasilia62070503***6304A1B2"
    )


def _make_http_error(status_code: int) -> HTTPError:
    response = Response()
    response.status_code = status_code
    error = HTTPError(response=response)
    return error


def _mock_preview_response(amount=10.00, amount_type="FIXED", init_type="DYNAMIC_QR_CODE"):
    return type(
        "BRCodePreviewResponseDTO",
        (),
        {
            "beneficiary": type(
                "Beneficiary",
                (),
                {
                    "holder_name": "Fulano de Tal",
                    "government_id": "12345678901",
                    "code": "001",
                    "agency": "0001",
                    "account": "12345",
                    "digit": "6",
                    "account_type": "checking",
                    "pix_key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "financial_account": None,
                },
            )(),
            "end_to_end_id": "E00000000202600001200AbCdEfGhIjKl",
            "qr_code": _valid_brcode(),
            "amount": amount,
            "amount_type": amount_type,
            "nominal_amount": amount,
            "discount_amount": None,
            "fine_amount": None,
            "interest_amount": None,
            "reduction_amount": None,
            "reconciliation_id": "6db5125deb834bc59009b3bd25aa323c",
            "status": "ACTIVE",
            "init_type": init_type,
            "key_id": "4004901d-bd85-4769-8e52-cb4c42c506dc",
            "schedule_at": None,
            "cash_amount": None,
            "cashier_type": None,
            "cashier_bank_code": None,
            "pix_pull_subscription_id": None,
            "model_dump": lambda self: {
                "end_to_end_id": "E00000000202600001200AbCdEfGhIjKl",
                "qr_code": _valid_brcode(),
                "beneficiary": {
                    "holder_name": "Fulano de Tal",
                    "government_id": "12345678901",
                    "code": "001",
                    "agency": "0001",
                    "account": "12345",
                    "digit": "6",
                    "account_type": "checking",
                    "pix_key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "financial_account": None,
                },
                "amount": amount,
                "amount_type": amount_type,
                "nominal_amount": amount,
                "discount_amount": None,
                "fine_amount": None,
                "interest_amount": None,
                "reduction_amount": None,
                "reconciliation_id": "6db5125deb834bc59009b3bd25aa323c",
                "status": "ACTIVE",
                "init_type": init_type,
                "key_id": "4004901d-bd85-4769-8e52-cb4c42c506dc",
                "schedule_at": None,
                "cash_amount": None,
                "cashier_type": None,
                "cashier_bank_code": None,
                "pix_pull_subscription_id": None,
            },
        },
    )()


# --- Success cases ---


@pytest.mark.asyncio
@patch("src.services.brcode_preview_service.settings")
async def test_execute_fixed_amount_success(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_banking_client.brcode_preview.return_value = _mock_preview_response(amount=10.00, amount_type="FIXED")
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": _valid_brcode()})

    assert result["action_success"] is True
    assert result["action_data"]["amount"] == 10.00
    assert result["action_data"]["amount_type"] == "FIXED"
    assert result["withdraw_amount"] == 10.00
    assert result["withdraw_end_to_end_id"] == "E00000000202600001200AbCdEfGhIjKl"
    mock_banking_client.brcode_preview.assert_awaited_once_with("primary-account", _valid_brcode())


@pytest.mark.asyncio
@patch("src.services.brcode_preview_service.settings")
async def test_execute_variable_amount_success(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_banking_client.brcode_preview.return_value = _mock_preview_response(amount=None, amount_type="VARIABLE")
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": _valid_brcode()})

    assert result["action_success"] is True
    assert result["action_data"]["amount"] is None
    assert result["action_data"]["amount_type"] == "VARIABLE"
    assert result["withdraw_amount"] is None


@pytest.mark.asyncio
@patch("src.services.brcode_preview_service.settings")
async def test_state_enrichment_maps_withdraw_fields(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_banking_client.brcode_preview.return_value = _mock_preview_response()
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": _valid_brcode()})

    assert result["withdraw_beneficiary"]["holderName"] == "Fulano de Tal"
    assert result["withdraw_beneficiary"]["governmentId"] == "12345678901"
    assert result["withdraw_beneficiary"]["code"] == "001"
    assert result["withdraw_beneficiary"]["agency"] == "0001"
    assert result["withdraw_beneficiary"]["account"] == "12345"
    assert result["withdraw_beneficiary"]["digit"] == "6"
    assert result["withdraw_beneficiary"]["accountType"] == "checking"
    assert result["withdraw_beneficiary"]["pixKey"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    assert result["withdraw_end_to_end_id"] == "E00000000202600001200AbCdEfGhIjKl"
    assert result["withdraw_qr_code"] == _valid_brcode()
    assert result["withdraw_init_type"] == "DYNAMIC_QR_CODE"
    assert result["withdraw_reconciliation_id"] == "6db5125deb834bc59009b3bd25aa323c"
    assert result["withdraw_amount_type"] == "FIXED"
    assert result["withdraw_nominal_amount"] == 10.00


# --- Validation error cases ---


@pytest.mark.asyncio
async def test_execute_brcode_missing(mock_banking_client):
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": None})

    assert result["action_success"] is False
    assert "required" in result["action_error"].lower()


@pytest.mark.asyncio
async def test_execute_brcode_empty_string(mock_banking_client):
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": ""})

    assert result["action_success"] is False
    assert "required" in result["action_error"].lower()


@pytest.mark.asyncio
async def test_execute_brcode_invalid_prefix(mock_banking_client):
    service = BRCodePreviewService(mock_banking_client)
    invalid_brcode = "999999br.gov.bcb.pix6304ABCD"

    result = await service.execute({"brcode": invalid_brcode})

    assert result["action_success"] is False
    assert "000201" in result["action_error"]


@pytest.mark.asyncio
async def test_execute_brcode_missing_gui(mock_banking_client):
    service = BRCodePreviewService(mock_banking_client)
    invalid_brcode = "000201265800140136a1b2c3d46304ABCD"

    result = await service.execute({"brcode": invalid_brcode})

    assert result["action_success"] is False
    assert "br.gov.bcb.pix" in result["action_error"]


@pytest.mark.asyncio
async def test_execute_brcode_invalid_crc(mock_banking_client):
    service = BRCodePreviewService(mock_banking_client)
    invalid_brcode = "00020126580014br.gov.bcb.pix0136a1b2c3d4520400005303986"

    result = await service.execute({"brcode": invalid_brcode})

    assert result["action_success"] is False
    assert "CRC" in result["action_error"]


# --- API error cases ---


@pytest.mark.asyncio
@patch("src.services.brcode_preview_service.settings")
async def test_execute_api_error_4xx(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = ""
    mock_banking_client.brcode_preview.side_effect = _make_http_error(400)
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": _valid_brcode()})

    assert result["action_success"] is False
    assert "action_error" in result


@pytest.mark.asyncio
@patch("src.services.brcode_preview_service.settings")
async def test_execute_api_error_retryable_with_fallback(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_banking_client.brcode_preview.side_effect = [
        _make_http_error(422),
        _mock_preview_response(),
    ]
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": _valid_brcode()})

    assert result["action_success"] is True
    assert mock_banking_client.brcode_preview.await_count == 2
    call_args = mock_banking_client.brcode_preview.call_args_list
    assert call_args[0][0][0] == "primary-account"
    assert call_args[1][0][0] == "fallback-account"


@pytest.mark.asyncio
@patch("src.services.brcode_preview_service.settings")
async def test_execute_api_error_retryable_fallback_also_fails(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = "primary-account"
    mock_settings.FIN_ACCOUNT_ID_FALLBACK = "fallback-account"
    mock_banking_client.brcode_preview.side_effect = [
        _make_http_error(422),
        _make_http_error(500),
    ]
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": _valid_brcode()})

    assert result["action_success"] is False


@pytest.mark.asyncio
@patch("src.services.brcode_preview_service.settings")
async def test_execute_fin_account_not_configured(mock_settings, mock_banking_client):
    mock_settings.FIN_ACCOUNT_ID = ""
    service = BRCodePreviewService(mock_banking_client)

    result = await service.execute({"brcode": _valid_brcode()})

    assert result["action_success"] is False
    assert "FIN_ACCOUNT_ID" in result["action_error"]


# --- Masking tests ---


def test_mask_cpf():
    result = BRCodePreviewService._mask_government_id("12345678901")
    assert result == "123.***.***-01"


def test_mask_cnpj():
    result = BRCodePreviewService._mask_government_id("12345678000199")
    assert result == "12.***.***/****-99"


def test_mask_unknown_format():
    result = BRCodePreviewService._mask_government_id("ABC")
    assert result == "ABC"
