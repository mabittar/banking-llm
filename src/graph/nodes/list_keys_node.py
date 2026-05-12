from ...infrastructure.banking_client import BankingClient
from ..state import GraphState


def create_list_keys_node(logger, banking_client: BankingClient):
    async def list_keys_node(state: GraphState) -> dict:
        logger.info("List keys node")
        fin_account_id = state.get("fin_account_id")
        try:
            if not fin_account_id:
                return {
                    "action_success": False,
                    "action_error": "fin_account_id is required",
                }

            result = await banking_client.list_active_pix_keys(fin_account_id)
            return {
                "action_success": True,
                "action_data": result.model_dump(),
            }
        except Exception as error:
            logger.error("Error listing PIX keys", exc_info=True)
            return {
                "action_success": False,
                "action_error": str(error),
            }

    return list_keys_node
