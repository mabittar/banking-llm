from ...core.logger import logger
from ...core.observability import domain_span
from ...services.response_service import ResponseService
from ..state import GraphState


def create_chat_response_node(response_service: ResponseService):
    async def chat_response_node(state: GraphState) -> dict:
        logger.info("Chat response node")
        with domain_span("llm.response.generate", **{"graph.node": "chatResponse"}):
            return await response_service.generate(state)

    return chat_response_node
