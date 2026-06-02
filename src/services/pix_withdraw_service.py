from decimal import Decimal, InvalidOperation

from requests import HTTPError

from ..core.config import settings
from ..core.logger import logger
from ..infrastructure.banking.banking_client import BankingClient

RETRYABLE_STATUS_CODES = {402, 422}


class PixWithdrawService:
    def __init__(self, banking_client: BankingClient):
        self._banking_client = banking_client

    async def execute(self, state: dict) -> dict:
        state = await self._enrich_state(state)

        validation_error = self._validate(state)
        if validation_error:
            return {"action_success": False, "action_error": validation_error}

        payload = self._build_payload(state)
        return await self._execute_with_fallback(payload)

    async def _enrich_state(self, state: dict) -> dict:
        """Auto-fetch key details when init_type is DICT and beneficiary is missing."""
        init_type = state.get("withdraw_init_type")
        pix_key = state.get("pix_key")

        if init_type == "DICT" and pix_key and not state.get("withdraw_beneficiary"):
            logger.info("Fetching pix key details for DICT transfer", pix_key=pix_key)
            fin_account_id = settings.FIN_ACCOUNT_ID
            if not fin_account_id:
                return state
            try:
                key_data = await self._banking_client.read_pix_key(
                    pix_key, fin_account_id
                )
                beneficiary = key_data.beneficiary
                state = {**state}
                state["withdraw_beneficiary"] = {
                    "holderName": beneficiary.holder_name,
                    "governmentId": beneficiary.government_id,
                    "code": beneficiary.code,
                    "agency": beneficiary.agency,
                    "account": beneficiary.account,
                    "digit": beneficiary.digit,
                    "accountType": beneficiary.account_type,
                    "pixKey": beneficiary.pix_key,
                }
                state["withdraw_end_to_end_id"] = key_data.end_to_end_id
                logger.info("Key details fetched", e2e=key_data.end_to_end_id)
            except Exception as e:
                logger.error("Failed to fetch pix key details", error=str(e))

        return state

    def _validate(self, state: dict) -> str | None:
        amount_error = self._validate_amount(state.get("withdraw_amount"))
        if amount_error:
            return amount_error

        init_type = state.get("withdraw_init_type")
        if not init_type:
            return "initType is required"

        if not settings.TRANSACTION_HASH_SECRET:
            return "Transaction hash secret not configured"

        beneficiary = state.get("withdraw_beneficiary")
        if not beneficiary:
            return "Beneficiary data is required"

        if init_type == "MANUAL":
            return self._validate_manual(beneficiary)
        elif init_type == "DICT":
            return self._validate_dict(state, beneficiary)
        elif init_type in ("STATIC_QR_CODE", "DYNAMIC_QR_CODE"):
            return self._validate_qr_code(state)
        else:
            return f"Invalid initType: {init_type}"

    def _validate_amount(self, raw_amount) -> str | None:
        if not raw_amount:
            return "Invalid amount: must be greater than zero"
        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, ValueError, TypeError):
            return "Invalid amount: value is not a valid number"
        if amount <= 0:
            return "Invalid amount: must be greater than zero"
        if amount.as_tuple().exponent < -2:
            return "Invalid amount: maximum of 2 decimal places allowed. Please round to cents (e.g. R$100.50)"
        return None

    def _validate_manual(self, beneficiary: dict) -> str | None:
        required = ["holderName", "governmentId", "code", "agency", "account", "digit"]
        missing = [f for f in required if not beneficiary.get(f)]
        if missing:
            return f"Beneficiary data is incomplete. Missing: {', '.join(missing)}"
        return None

    def _validate_dict(self, state: dict, beneficiary: dict) -> str | None:
        if not state.get("withdraw_end_to_end_id"):
            return "end_to_end_id is required for non-manual transfers"
        if not beneficiary.get("pixKey"):
            return "pixKey is required for DICT transfers"
        return None

    def _validate_qr_code(self, state: dict) -> str | None:
        if not state.get("withdraw_end_to_end_id"):
            return "end_to_end_id is required for non-manual transfers"
        if not state.get("withdraw_qr_code"):
            return "qrCode is required for QR Code transfers"
        if not state.get("withdraw_reconciliation_id"):
            return "reconciliationId is required for QR Code transfers"
        if not state.get("withdraw_key_id"):
            return "keyId is required for QR Code transfers"
        return None

    def _build_payload(self, state: dict) -> dict:
        init_type = state.get("withdraw_init_type")
        beneficiary = state.get("withdraw_beneficiary", {})

        amount = Decimal(str(state.get("withdraw_amount", 0))).quantize(Decimal("0.01"))

        payload: dict = {
            "beneficiary": beneficiary,
            "amount": float(amount),
            "initType": init_type,
        }

        if state.get("withdraw_end_to_end_id"):
            payload["endToEndId"] = state["withdraw_end_to_end_id"]
        if state.get("withdraw_additional_info"):
            payload["additionalInfo"] = state["withdraw_additional_info"]

        if init_type in ("STATIC_QR_CODE", "DYNAMIC_QR_CODE"):
            if state.get("withdraw_qr_code"):
                payload["qrCode"] = state["withdraw_qr_code"]
            if state.get("withdraw_reconciliation_id"):
                payload["reconciliationId"] = state["withdraw_reconciliation_id"]
            if state.get("withdraw_key_id"):
                payload["keyId"] = state["withdraw_key_id"]
            if state.get("withdraw_amount_type"):
                payload["amountType"] = state["withdraw_amount_type"]
            if state.get("withdraw_nominal_amount"):
                nominal = Decimal(str(state["withdraw_nominal_amount"])).quantize(
                    Decimal("0.01")
                )
                payload["nominalAmount"] = float(nominal)

        return payload

    async def _execute_with_fallback(self, payload: dict) -> dict:
        fin_account_id = settings.FIN_ACCOUNT_ID
        if not fin_account_id:
            return {
                "action_success": False,
                "action_error": "FIN_ACCOUNT_ID not configured",
            }

        try:
            result = await self._banking_client.pix_transfer(fin_account_id, payload)
            return {"action_success": True, "action_data": result.model_dump()}
        except Exception as primary_error:
            if self._is_retryable(primary_error) and settings.FIN_ACCOUNT_ID_FALLBACK:
                logger.warning(
                    "Primary account failed for withdraw, retrying with fallback",
                    error=str(primary_error),
                )
                try:
                    result = await self._banking_client.pix_transfer(
                        settings.FIN_ACCOUNT_ID_FALLBACK, payload
                    )
                    return {"action_success": True, "action_data": result.model_dump()}
                except Exception as fallback_error:
                    return {
                        "action_success": False,
                        "action_error": str(fallback_error),
                    }
            return {"action_success": False, "action_error": str(primary_error)}

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        if isinstance(error, HTTPError) and error.response is not None:
            return error.response.status_code in RETRYABLE_STATUS_CODES
        return False
