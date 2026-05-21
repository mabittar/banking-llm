from langchain_core.messages import AnyMessage

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
            result: IntentResult = await self._llm_service.generate_structured(system_prompt, user_prompt, IntentResult)

            return {
                "command": result.intent,
                "pix_key": result.pix_key,
            }
        except Exception as error:
            return {"command": "unknown", "action_error": str(error)}
