from langchain_core.messages import AIMessage

from ...core.logger import logger
from ...core.observability import domain_span
from ...core.observability.domain_metrics import record_guardrail_block
from ...services.guardrail_service import GuardrailService
from ..state import GraphState

BLOCKED_MESSAGE = "Não foi possível processar sua solicitação. Por favor, reformule sua pergunta sobre operações PIX."


def create_guardrail_node(guardrail_service: GuardrailService):
    async def guardrail_node(state: GraphState) -> dict:
        messages = state.get("messages", [])
        if not messages:
            return {"is_blocked": False}

        user_input = str(messages[-1].content)
        logger.info("Guardrail check", input_length=len(user_input))
        with domain_span(
            "graph.guardrail.check", **{"graph.node": "guardrail"}
        ) as span:
            result = await guardrail_service.check(user_input)
            blocked = bool(result["is_blocked"])
            span.set_attribute("guardrail.blocked", blocked)
            record_guardrail_block(blocked)
            return {"is_blocked": result["is_blocked"]}

    return guardrail_node


def blocked_response_node(state: GraphState) -> dict:
    return {"messages": [AIMessage(content=BLOCKED_MESSAGE)]}
