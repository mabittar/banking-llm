import re

from ...core.logger import logger
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


def create_identify_intent_node(intent_service: IntentService):
    async def identify_intent(state: GraphState) -> dict:
        logger.info("Identify intent")
        messages = state.get("messages", [])

        if state.get("awaiting_amount") and messages:
            last_text = str(messages[-1].content)
            amount = _extract_amount(last_text)
            if amount:
                logger.info(
                    "Continuation detected",
                    awaiting_amount=True,
                    extracted_amount=amount,
                )
                return {
                    "command": "pix_payment",
                    "withdraw_amount": amount,
                    "awaiting_amount": False,
                }

        result = await intent_service.classify(messages)

        command = result.get("command", "unknown")
        pix_key = result.get("pix_key")
        logger.info("Intent identified", intent=command, pix_key=pix_key)

        return result

    return identify_intent
