from ..infrastructure.banking.banking_client import BankingClient


class PixKeyService:
    def __init__(self, banking_client: BankingClient):
        self._banking_client = banking_client

    async def list_keys(self, fin_account_id: str | None) -> dict:
        try:
            if not fin_account_id:
                return {"action_success": False, "action_error": "fin_account_id is required"}

            result = await self._banking_client.list_active_pix_keys(fin_account_id)
            return {"action_success": True, "action_data": result.model_dump()}
        except Exception as error:
            return {"action_success": False, "action_error": str(error)}

    async def read_key(self, fin_account_id: str | None, pix_key: str | None) -> dict:
        try:
            if not fin_account_id or not pix_key:
                return {"action_success": False, "action_error": "fin_account_id and pix_key are required"}

            result = await self._banking_client.read_pix_key(pix_key, fin_account_id)
            return {"action_success": True, "action_data": result.model_dump()}
        except Exception as error:
            return {"action_success": False, "action_error": str(error)}
