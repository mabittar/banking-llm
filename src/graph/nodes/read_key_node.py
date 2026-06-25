from ...core.logger import logger
from ...core.observability import domain_span
from ...services.pix_key_service import PixKeyService
from ..state import GraphState


def create_read_key_node(pix_key_service: PixKeyService):
    async def read_key_node(state: GraphState) -> dict:
        logger.info("Read key node")
        with domain_span(
            "pix.keys.read",
            **{"graph.node": "readKey", "pix.key.masked": state.get("pix_key")},
        ):
            return await pix_key_service.read_key(state.get("pix_key"))

    return read_key_node
