import re

from requests import HTTPError

from ..core.config import settings
from ..core.logger import logger
from ..infrastructure.banking.banking_client import BankingClient

RETRYABLE_STATUS_CODES = {404, 402, 422}

BRCODE_CRC_PATTERN = re.compile(r"6304[0-9A-Fa-f]{4}$")


class BRCodePreviewService:
    def __init__(self, banking_client: BankingClient):
        self._banking_client = banking_client

    async def execute(self, state: dict) -> dict:
        brcode = state.get("brcode")
        if not brcode:
            return {
                "action_success": False,
                "action_error": "BRCode payload is required. Please provide the QR Code content.",
            }

        validation_error = self._validate_brcode(brcode)
        if validation_error:
            return {"action_success": False, "action_error": validation_error}

        return await self._execute_with_fallback(brcode)

    def _validate_brcode(self, brcode: str) -> str | None:
        if not brcode.startswith("000201"):
            return "Invalid BRCode: payload must start with '000201' (Payload Format Indicator)."

        if "br.gov.bcb.pix" not in brcode:
            return "Invalid BRCode: payload must contain 'br.gov.bcb.pix' (PIX GUI)."

        if not BRCODE_CRC_PATTERN.search(brcode):
            return "Invalid BRCode: payload must end with CRC checksum (tag '6304' + 4 hex characters)."

        return None

    async def _execute_with_fallback(self, brcode: str) -> dict:
        fin_account_id = settings.FIN_ACCOUNT_ID
        if not fin_account_id:
            return {
                "action_success": False,
                "action_error": "FIN_ACCOUNT_ID not configured",
            }

        try:
            response = await self._banking_client.brcode_preview(fin_account_id, brcode)
            return self._enrich_state(response)
        except Exception as primary_error:
            if self._is_retryable(primary_error) and settings.FIN_ACCOUNT_ID_FALLBACK:
                logger.warning(
                    "Primary account failed for brcode preview, retrying with fallback",
                    error=str(primary_error),
                )
                try:
                    response = await self._banking_client.brcode_preview(
                        settings.FIN_ACCOUNT_ID_FALLBACK, brcode
                    )
                    return self._enrich_state(response)
                except Exception as fallback_error:
                    return {
                        "action_success": False,
                        "action_error": str(fallback_error),
                    }
            return {"action_success": False, "action_error": str(primary_error)}

    def _enrich_state(self, response) -> dict:
        beneficiary = response.beneficiary
        data = response.model_dump()
        data["beneficiary"]["government_id"] = self._mask_government_id(
            beneficiary.government_id
        )

        return {
            "action_success": True,
            "action_data": data,
            "withdraw_beneficiary": {
                "holderName": beneficiary.holder_name,
                "governmentId": beneficiary.government_id,
                "code": beneficiary.code,
                "agency": beneficiary.agency,
                "account": beneficiary.account,
                "digit": beneficiary.digit,
                "accountType": beneficiary.account_type,
                "pixKey": beneficiary.pix_key,
            },
            "withdraw_end_to_end_id": response.end_to_end_id,
            "withdraw_qr_code": response.qr_code,
            "withdraw_init_type": response.init_type,
            "withdraw_reconciliation_id": response.reconciliation_id,
            "withdraw_key_id": response.key_id,
            "withdraw_amount_type": response.amount_type,
            "withdraw_nominal_amount": response.nominal_amount,
            "withdraw_amount": response.amount,
        }

    @staticmethod
    def _mask_government_id(gov_id: str) -> str:
        if len(gov_id) == 11:
            return f"{gov_id[:3]}.***.***-{gov_id[-2:]}"
        elif len(gov_id) == 14:
            return f"{gov_id[:2]}.***.***/****-{gov_id[-2:]}"
        return gov_id

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        if isinstance(error, HTTPError) and error.response is not None:
            return error.response.status_code in RETRYABLE_STATUS_CODES
        return False
