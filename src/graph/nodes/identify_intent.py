import re

from ...core.logger import logger
from ...core.observability import domain_span
from ...services.intent_service import IntentService
from ..state import GraphState

_AMOUNT_PATTERN = re.compile(r"(\d+[.,]\d{1,2}|\d+)")


def _extract_amount(text: str) -> float | None:
    match = _AMOUNT_PATTERN.search(text)
    if match:
        value = match.group(1).replace(",", ".")
        amount = float(value)
        if amount > 0:
            return amount
    return None


def _handle_continuation(state: GraphState, messages: list) -> dict | None:
    """Resolve a pending amount from the user's last message, if any."""
    if not (state.get("awaiting_amount") and messages):
        return None
    amount = _extract_amount(str(messages[-1].content))
    if not amount:
        return None
    logger.info("Continuation detected", awaiting_amount=True, extracted_amount=amount)
    return {
        "command": "pix_payment",
        "withdraw_amount": amount,
        "awaiting_amount": False,
    }


def create_identify_intent_node(intent_service: IntentService):
    async def identify_intent(state: GraphState) -> dict:
        logger.info("Identify intent")
        messages = state.get("messages", [])
        with domain_span(
            "graph.intent.identify", **{"graph.node": "identifyIntent"}
        ) as span:
            continuation = _handle_continuation(state, messages)
            if continuation:
                span.set_attribute("pix.intent", continuation["command"])
                return continuation

            result = await intent_service.classify(messages)
            command = result.get("command", "unknown")
            logger.info(
                "Intent identified", intent=command, pix_key=result.get("pix_key")
            )
            span.set_attribute("pix.intent", command)
            return result

    return identify_intent
