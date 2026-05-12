from ...core.logger import logger
from ...infrastructure.llm_service import LLMService
from ..prompts.identify_intent import IntentResult, get_system_prompt, get_user_prompt
from ..state import GraphState


def create_identify_intent_node(llm_service: LLMService):
    async def identify_intent(state: GraphState) -> dict:
        logger.info("Identify intent")
        messages = state.get("messages", [])
        input_text = ""
        try:
            if messages:
                last_message = messages[-1]
                input_text = str(last_message.content)

            system_prompt = get_system_prompt()
            user_prompt = get_user_prompt(input_text)
            result: IntentResult = await llm_service.generate_structured(
                system_prompt, user_prompt, IntentResult
            )

            logger.info(
                "Intent identified",
                intent=result.intent,
                fin_account_id=result.fin_account_id,
                pix_key=result.pix_key,
            )

            return {
                "command": result.intent,
                "fin_account_id": result.fin_account_id,
                "pix_key": result.pix_key,
            }
        except Exception as error:
            logger.error("Error identifying intent", exc_info=True)
            return {"command": "unknown", "action_error": str(error)}

    return identify_intent
