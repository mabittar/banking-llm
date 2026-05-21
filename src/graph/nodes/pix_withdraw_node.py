from ...core.logger import logger
from ...services.pix_withdraw_service import PixWithdrawService
from ..state import GraphState


def create_pix_withdraw_node(pix_withdraw_service: PixWithdrawService):
    async def pix_withdraw_node(state: GraphState) -> dict:
        logger.info(
            "Pix withdraw node",
            pix_key=state.get("pix_key"),
            withdraw_amount=str(state.get("withdraw_amount")),
            withdraw_init_type=state.get("withdraw_init_type"),
        )
        return await pix_withdraw_service.execute(state)

    return pix_withdraw_node
