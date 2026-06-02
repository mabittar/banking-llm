from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.services.pix_payment_service import PixPaymentService


@pytest.fixture
def mock_preview_service():
    return AsyncMock()


@pytest.fixture
def mock_withdraw_service():
    return AsyncMock()


@pytest.fixture
def service(mock_preview_service, mock_withdraw_service):
    return PixPaymentService(mock_preview_service, mock_withdraw_service)


def _valid_brcode() -> str:
    return (
        "00020126580014br.gov.bcb.pix0136a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        "520400005303986540510.005802BR5913Test Merchant6008Brasilia62070503***6304A1B2"
    )


def _preview_success(status="ACTIVE", amount=Decimal("150.00"), amount_type="FIXED"):
    return {
        "action_success": True,
        "action_data": {
            "status": status,
            "beneficiary": {"holder_name": "Fulano", "government_id": "123.***.***-01"},
            "end_to_end_id": "E00000000202600001200AbCdEfGhIjKl",
        },
        "withdraw_beneficiary": {
            "holderName": "Fulano",
            "governmentId": "12345678901",
            "code": "001",
            "agency": "0001",
            "account": "12345",
            "digit": "6",
            "accountType": "checking",
            "pixKey": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        },
        "withdraw_end_to_end_id": "E00000000202600001200AbCdEfGhIjKl",
        "withdraw_qr_code": _valid_brcode(),
        "withdraw_init_type": "DYNAMIC_QR_CODE",
        "withdraw_reconciliation_id": "6db5125deb834bc59009b3bd25aa323c",
        "withdraw_amount_type": amount_type,
        "withdraw_nominal_amount": amount,
        "withdraw_amount": amount,
    }


class TestPixPaymentServiceActiveFixed:
    @pytest.mark.asyncio
    async def test_active_fixed_executes_payment(
        self, service, mock_preview_service, mock_withdraw_service
    ):
        state = {"brcode": _valid_brcode()}
        mock_preview_service.execute.return_value = _preview_success()
        mock_withdraw_service.execute.return_value = {
            "action_success": True,
            "action_data": {"uuid": "tx-123"},
        }

        result = await service.execute(state)

        assert result["action_success"] is True
        mock_withdraw_service.execute.assert_called_once()


class TestPixPaymentServiceActiveCustom:
    @pytest.mark.asyncio
    async def test_custom_with_amount_executes_payment(
        self, service, mock_preview_service, mock_withdraw_service
    ):
        state = {"brcode": _valid_brcode(), "withdraw_amount": Decimal("50.00")}
        mock_preview_service.execute.return_value = _preview_success(
            amount_type="CUSTOM", amount=None
        )
        mock_withdraw_service.execute.return_value = {
            "action_success": True,
            "action_data": {"uuid": "tx-456"},
        }

        result = await service.execute(state)

        assert result["action_success"] is True
        mock_withdraw_service.execute.assert_called_once()
        call_state = mock_withdraw_service.execute.call_args[0][0]
        assert call_state["withdraw_amount"] == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_custom_without_amount_returns_awaiting(
        self, service, mock_preview_service, mock_withdraw_service
    ):
        state = {"brcode": _valid_brcode()}
        mock_preview_service.execute.return_value = _preview_success(
            amount_type="CUSTOM", amount=None
        )

        result = await service.execute(state)

        assert result["awaiting_amount"] is True
        assert result["action_success"] is True
        mock_withdraw_service.execute.assert_not_called()


class TestPixPaymentServiceStatusBlocked:
    @pytest.mark.asyncio
    async def test_paid_status_blocks_payment(
        self, service, mock_preview_service, mock_withdraw_service
    ):
        state = {"brcode": _valid_brcode()}
        mock_preview_service.execute.return_value = _preview_success(status="PAID")

        result = await service.execute(state)

        assert result["action_success"] is False
        assert result["brcode_status"] == "PAID"
        assert "PAGO" in result["action_error"]
        mock_withdraw_service.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_expired_status_blocks_payment(
        self, service, mock_preview_service, mock_withdraw_service
    ):
        state = {"brcode": _valid_brcode()}
        mock_preview_service.execute.return_value = _preview_success(status="EXPIRED")

        result = await service.execute(state)

        assert result["action_success"] is False
        assert result["brcode_status"] == "EXPIRED"
        assert "EXPIRADO" in result["action_error"]
        mock_withdraw_service.execute.assert_not_called()


class TestPixPaymentServiceContinuation:
    @pytest.mark.asyncio
    async def test_continuation_skips_preview(
        self, service, mock_preview_service, mock_withdraw_service
    ):
        state = {
            "brcode": _valid_brcode(),
            "withdraw_end_to_end_id": "E00000000202600001200AbCdEfGhIjKl",
            "withdraw_amount": Decimal("75.00"),
            "withdraw_beneficiary": {"holderName": "Fulano"},
            "withdraw_init_type": "DYNAMIC_QR_CODE",
            "withdraw_qr_code": _valid_brcode(),
            "withdraw_reconciliation_id": "abc123",
        }
        mock_withdraw_service.execute.return_value = {
            "action_success": True,
            "action_data": {"uuid": "tx-789"},
        }

        result = await service.execute(state)

        assert result["action_success"] is True
        mock_preview_service.execute.assert_not_called()
        mock_withdraw_service.execute.assert_called_once()


class TestPixPaymentServiceErrors:
    @pytest.mark.asyncio
    async def test_preview_failure_returns_error(
        self, service, mock_preview_service, mock_withdraw_service
    ):
        state = {"brcode": _valid_brcode()}
        mock_preview_service.execute.return_value = {
            "action_success": False,
            "action_error": "BRCode payload is required.",
        }

        result = await service.execute(state)

        assert result["action_success"] is False
        assert "required" in result["action_error"]
        mock_withdraw_service.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_amount_type_returns_error(
        self, service, mock_preview_service, mock_withdraw_service
    ):
        state = {"brcode": _valid_brcode()}
        mock_preview_service.execute.return_value = _preview_success(
            amount_type="UNKNOWN_TYPE", amount=None
        )

        result = await service.execute(state)

        assert result["action_success"] is False
        assert "desconhecido" in result["action_error"]
        mock_withdraw_service.execute.assert_not_called()
