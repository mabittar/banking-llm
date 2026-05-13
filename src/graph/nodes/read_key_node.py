from ...infrastructure.banking.banking_client import BankingClient
from ..state import GraphState


def create_read_key_node(logger, banking_client: BankingClient):
    async def read_key_node(state: GraphState) -> dict:
        logger.info("Read key node")
        fin_account_id = state.get("fin_account_id")
        pix_key = state.get("pix_key")
        try:
            if not fin_account_id or not pix_key:
                return {
                    "action_success": False,
                    "action_error": "fin_account_id and pix_key are required",
                }

            result = await banking_client.read_pix_key(pix_key, fin_account_id)
            return {
                "action_success": True,
                "action_data": result.model_dump(),
            }
        except Exception as error:
            logger.error("Error reading PIX key", exc_info=True)
            return {
                "action_success": False,
                "action_error": str(error),
            }

    return read_key_node
