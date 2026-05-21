from ...core.logger import logger
from ...services.intent_service import IntentService
from ..state import GraphState


def create_identify_intent_node(intent_service: IntentService):
    async def identify_intent(state: GraphState) -> dict:
        logger.info("Identify intent")
        messages = state.get("messages", [])
        result = await intent_service.classify(messages)

        command = result.get("command", "unknown")
        pix_key = result.get("pix_key")
        logger.info("Intent identified", intent=command, pix_key=pix_key)

        return result

    return identify_intent
