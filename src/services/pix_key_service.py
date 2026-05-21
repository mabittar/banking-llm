from requests import HTTPError

from ..core.config import settings
from ..core.logger import logger
from ..infrastructure.banking.banking_client import BankingClient

RETRYABLE_STATUS_CODES = {404, 402, 422}


class PixKeyService:
    def __init__(self, banking_client: BankingClient):
        self._banking_client = banking_client

    async def list_keys(self) -> dict:
        return await self._execute_with_fallback(
            self._banking_client.list_active_pix_keys
        )

    async def read_key(self, pix_key: str | None) -> dict:
        if not pix_key:
            return {"action_success": False, "action_error": "pix_key is required"}
        return await self._execute_with_fallback(
            self._banking_client.read_pix_key, pix_key
        )

    async def _execute_with_fallback(self, operation, *args) -> dict:
        fin_account_id = settings.FIN_ACCOUNT_ID
        if not fin_account_id:
            return {
                "action_success": False,
                "action_error": "FIN_ACCOUNT_ID not configured",
            }

        try:
            result = await self._call_operation(operation, fin_account_id, *args)
            return {"action_success": True, "action_data": result.model_dump()}
        except Exception as primary_error:
            if self._is_retryable(primary_error) and settings.FIN_ACCOUNT_ID_FALLBACK:
                logger.warning(
                    "Primary account failed, retrying with fallback",
                    error=str(primary_error),
                )
                try:
                    result = await self._call_operation(
                        operation, settings.FIN_ACCOUNT_ID_FALLBACK, *args
                    )
                    return {"action_success": True, "action_data": result.model_dump()}
                except Exception as fallback_error:
                    return {
                        "action_success": False,
                        "action_error": str(fallback_error),
                    }
            return {"action_success": False, "action_error": str(primary_error)}

    async def _call_operation(self, operation, fin_account_id: str, *args):
        if operation == self._banking_client.read_pix_key:
            return await operation(args[0], fin_account_id)
        return await operation(fin_account_id)

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        if isinstance(error, HTTPError) and error.response is not None:
            return error.response.status_code in RETRYABLE_STATUS_CODES
        return False
