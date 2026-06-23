from langchain_core.messages import AIMessage

from ..graph.prompts.chat_response import (
    MessageResult,
    get_system_prompt,
    get_user_prompt,
)
from ..graph.state import GraphState
from ..infrastructure.llm_service import LLMService


class ResponseService:
    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    async def generate(self, state: GraphState) -> dict:
        try:
            command = state.get("command", "unknown")
            action_success = state.get("action_success")
            action_data = state.get("action_data")
            action_error = state.get("action_error")

            scenario = self._resolve_scenario(command, action_success, state)

            context = {
                "pix_key": state.get("pix_key"),
                "action_data": action_data,
                "action_error": action_error,
            }

            system_prompt = get_system_prompt()
            user_prompt = get_user_prompt(scenario, context)
            result: MessageResult = await self._llm_service.generate_structured(
                system_prompt, user_prompt, MessageResult
            )

            return {"messages": [AIMessage(content=result.message)]}
        except Exception:
            fallback = "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente."
            return {"messages": [AIMessage(content=fallback)]}

    def _resolve_scenario(
        self, command: str, action_success: bool | None, state: GraphState
    ) -> str:
        if command == "unknown":
            return "unknown"

        if command == "brcode_ambiguous":
            return "brcode_ambiguous_success"

        if command == "pix_payment":
            if state.get("awaiting_amount"):
                return "pix_payment_awaiting"
            if state.get("brcode_status") in ("PAID", "EXPIRED"):
                return "pix_payment_blocked"
            if action_success:
                return "pix_payment_success"
            return "pix_payment_error"

        if action_success:
            return f"{command}_success"
        return f"{command}_error"
