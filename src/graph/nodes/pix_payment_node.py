from ...core.logger import logger
from ...services.pix_payment_service import PixPaymentService
from ..state import GraphState


def create_pix_payment_node(pix_payment_service: PixPaymentService):
    async def pix_payment_node(state: GraphState) -> dict:
        logger.info(
            "Pix payment node",
            brcode=state.get("brcode", "")[:30] if state.get("brcode") else None,
            withdraw_amount=str(state.get("withdraw_amount")) if state.get("withdraw_amount") else None,
        )
        return await pix_payment_service.execute(state)

    return pix_payment_node
