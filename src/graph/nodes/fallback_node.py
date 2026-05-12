from ...core.logger import logger
from ..state import GraphState


def fallback_node(state: GraphState) -> dict:
    logger.info("Fallback node")
    return {
        "output": "",
        "action_success": True,
    }
