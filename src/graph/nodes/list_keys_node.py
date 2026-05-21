from ...core.logger import logger
from ...services.pix_key_service import PixKeyService
from ..state import GraphState


def create_list_keys_node(pix_key_service: PixKeyService):
    async def list_keys_node(state: GraphState) -> dict:
        logger.info("List keys node")
        return await pix_key_service.list_keys()

    return list_keys_node
