from langgraph.graph import END, START, StateGraph

from ..services.brcode_preview_service import BRCodePreviewService
from ..services.guardrail_service import GuardrailService
from ..services.intent_service import IntentService
from ..services.pix_key_service import PixKeyService
from ..services.pix_payment_service import PixPaymentService
from ..services.pix_withdraw_service import PixWithdrawService
from ..services.response_service import ResponseService
from .nodes.brcode_preview_node import create_brcode_preview_node
from .nodes.chat_response_node import create_chat_response_node
from .nodes.fallback_node import fallback_node
from .nodes.guardrail_node import blocked_response_node, create_guardrail_node
from .nodes.identify_intent import create_identify_intent_node
from .nodes.list_keys_node import create_list_keys_node
from .nodes.pix_payment_node import create_pix_payment_node
from .nodes.pix_withdraw_node import create_pix_withdraw_node
from .nodes.read_key_node import create_read_key_node
from .state import GraphState


def route_guardrail(state: GraphState) -> str:
    if state.get("is_blocked"):
        return "blocked"
    return "safe"


def route_intent(state: GraphState) -> str:
    command = state.get("command", "unknown")
    if command == "list_keys":
        return "list_keys"
    elif command == "read_key":
        return "read_key"
    elif command == "pix_withdraw":
        return "pix_withdraw"
    elif command == "brcode_preview":
        return "brcode_preview"
    elif command == "pix_payment":
        return "pix_payment"
    elif command == "brcode_ambiguous":
        return "brcode_ambiguous"
    return "fallback"


def build_graph(
    intent_service: IntentService,
    pix_key_service: PixKeyService,
    pix_withdraw_service: PixWithdrawService,
    brcode_preview_service: BRCodePreviewService,
    pix_payment_service: PixPaymentService,
    response_service: ResponseService,
    guardrail_service: GuardrailService,
    logger,
    checkpointer=None,
):
    workflow = StateGraph(GraphState)

    workflow.add_node("guardrail", create_guardrail_node(guardrail_service))
    workflow.add_node("blockedResponse", blocked_response_node)
    workflow.add_node("identifyIntent", create_identify_intent_node(intent_service))
    workflow.add_node("listKeys", create_list_keys_node(pix_key_service))
    workflow.add_node("readKey", create_read_key_node(pix_key_service))
    workflow.add_node("pixWithdraw", create_pix_withdraw_node(pix_withdraw_service))
    workflow.add_node("brcodePreview", create_brcode_preview_node(brcode_preview_service))
    workflow.add_node("pixPayment", create_pix_payment_node(pix_payment_service))
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("chatResponse", create_chat_response_node(response_service))

    workflow.add_edge(START, "guardrail")
    workflow.add_conditional_edges(
        "guardrail",
        route_guardrail,
        {
            "blocked": "blockedResponse",
            "safe": "identifyIntent",
        },
    )
    workflow.add_edge("blockedResponse", END)

    workflow.add_conditional_edges(
        "identifyIntent",
        route_intent,
        {
            "list_keys": "listKeys",
            "read_key": "readKey",
            "pix_withdraw": "pixWithdraw",
            "brcode_preview": "brcodePreview",
            "pix_payment": "pixPayment",
            "brcode_ambiguous": "fallback",
            "fallback": "fallback",
        },
    )

    workflow.add_edge("listKeys", "chatResponse")
    workflow.add_edge("readKey", "chatResponse")
    workflow.add_edge("pixWithdraw", "chatResponse")
    workflow.add_edge("brcodePreview", "chatResponse")
    workflow.add_edge("pixPayment", "chatResponse")
    workflow.add_edge("fallback", "chatResponse")
    workflow.add_edge("chatResponse", END)

    return workflow.compile(checkpointer=checkpointer)
