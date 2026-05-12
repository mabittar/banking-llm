from langchain_core.messages import AIMessage

from ...core.logger import logger
from ...infrastructure.llm_service import LLMService
from ..prompts.chat_response import MessageResult, get_system_prompt, get_user_prompt
from ..state import GraphState


def create_chat_response_node(llm_service: LLMService):
    async def chat_response_node(state: GraphState) -> dict:
        logger.info("Chat response node")
        try:
            command = state.get("command", "unknown")
            action_success = state.get("action_success")
            action_data = state.get("action_data")
            action_error = state.get("action_error")

            if command == "unknown":
                scenario = "unknown"
            elif action_success:
                scenario = f"{command}_success"
            else:
                scenario = f"{command}_error"

            context = {
                "fin_account_id": state.get("fin_account_id"),
                "pix_key": state.get("pix_key"),
                "action_data": action_data,
                "action_error": action_error,
            }

            system_prompt = get_system_prompt()
            user_prompt = get_user_prompt(scenario, context)
            result: MessageResult = await llm_service.generate_structured(
                system_prompt, user_prompt, MessageResult
            )

            return {"messages": [AIMessage(content=result.message)]}
        except Exception:
            logger.error("Error in chat response node", exc_info=True)
            fallback = "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente."
            return {"messages": [AIMessage(content=fallback)]}

    return chat_response_node
