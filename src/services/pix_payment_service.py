from ..core.logger import logger
from ..services.brcode_preview_service import BRCodePreviewService
from ..services.pix_withdraw_service import PixWithdrawService


class PixPaymentService:
    def __init__(
        self,
        brcode_preview_service: BRCodePreviewService,
        pix_withdraw_service: PixWithdrawService,
    ):
        self._preview_service = brcode_preview_service
        self._withdraw_service = pix_withdraw_service

    async def execute(self, state: dict) -> dict:
        logger.info(
            "Pix payment flow started",
            brcode=state.get("brcode", "")[:30] if state.get("brcode") else None,
            has_amount=state.get("withdraw_amount") is not None,
        )

        if self._is_continuation(state):
            return await self._withdraw_service.execute(state)

        preview_result = await self._preview_service.execute(state)
        if not preview_result.get("action_success"):
            return preview_result

        status_result = self._validate_status(preview_result)
        if status_result:
            return status_result

        return await self._resolve_amount_and_pay(state, preview_result)

    def _is_continuation(self, state: dict) -> bool:
        return bool(state.get("withdraw_end_to_end_id") and state.get("withdraw_amount"))

    _UNPAYABLE_STATUSES = {"PAID", "EXPIRED"}

    def _validate_status(self, preview_result: dict) -> dict | None:
        status = preview_result.get("action_data", {}).get("status", "UNKNOWN")

        if status not in self._UNPAYABLE_STATUSES:
            return None

        if status == "PAID":
            logger.warning("QR Code status blocked", status=status)
            return {
                **preview_result,
                "action_success": False,
                "action_error": "O QR Code informado possui status PAGO. Não é possível realizar o pagamento.",
                "brcode_status": "PAID",
            }

        logger.warning("QR Code status blocked", status=status)
        return {
            **preview_result,
            "action_success": False,
            "action_error": "O QR Code informado possui status EXPIRADO. Não é possível realizar o pagamento.",
            "brcode_status": "EXPIRED",
        }

    async def _resolve_amount_and_pay(self, state: dict, preview_result: dict) -> dict:
        amount_type = preview_result.get("withdraw_amount_type")
        amount = preview_result.get("withdraw_amount") or state.get("withdraw_amount")

        if amount_type == "FIXED":
            enriched = {**state, **preview_result}
            return await self._withdraw_service.execute(enriched)

        if amount_type == "CUSTOM":
            if amount and amount > 0:
                enriched = {**state, **preview_result, "withdraw_amount": amount}
                return await self._withdraw_service.execute(enriched)
            logger.info("Awaiting amount from user", amount_type=amount_type)
            return {**preview_result, "awaiting_amount": True}

        return {
            **preview_result,
            "action_success": False,
            "action_error": f"Tipo de valor desconhecido: {amount_type}",
        }
