from langchain_core.messages import AnyMessage

from ..core.logger import logger
from ..graph.prompts.identify_intent import (
    IntentResult,
    get_system_prompt,
    get_user_prompt,
)
from ..infrastructure.llm_service import LLMService


class IntentService:
    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    async def classify(self, messages: list[AnyMessage]) -> dict:
        try:
            input_text = ""
            if messages:
                last_message = messages[-1]
                input_text = str(last_message.content)

            system_prompt = get_system_prompt()
            user_prompt = get_user_prompt(input_text)
            result: IntentResult = await self._llm_service.generate_structured(
                system_prompt, user_prompt, IntentResult
            )

            state_update = {
                "command": result.intent,
                "pix_key": result.pix_key,
            }

            if result.intent == "pix_withdraw":
                if result.amount is not None:
                    state_update["withdraw_amount"] = result.amount
                if result.pix_key:
                    state_update["withdraw_init_type"] = "DICT"

            logger.info("Intent classified", **state_update)
            return state_update
        except Exception as error:
            return {"command": "unknown", "action_error": str(error)}
