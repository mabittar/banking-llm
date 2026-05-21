from ...core.logger import logger
from ...services.brcode_preview_service import BRCodePreviewService
from ..state import GraphState


def create_brcode_preview_node(brcode_preview_service: BRCodePreviewService):
    async def brcode_preview_node(state: GraphState) -> dict:
        logger.info(
            "BRCode preview node",
            brcode=state.get("brcode", "")[:30] if state.get("brcode") else None,
        )
        return await brcode_preview_service.execute(state)

    return brcode_preview_node
