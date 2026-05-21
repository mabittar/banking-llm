from langgraph.graph import END, START, StateGraph

from ..services.intent_service import IntentService
from ..services.pix_key_service import PixKeyService
from ..services.pix_withdraw_service import PixWithdrawService
from ..services.response_service import ResponseService
from .nodes.chat_response_node import create_chat_response_node
from .nodes.fallback_node import fallback_node
from .nodes.identify_intent import create_identify_intent_node
from .nodes.list_keys_node import create_list_keys_node
from .nodes.pix_withdraw_node import create_pix_withdraw_node
from .nodes.read_key_node import create_read_key_node
from .state import GraphState


def route_intent(state: GraphState) -> str:
    command = state.get("command", "unknown")
    if command == "list_keys":
        return "list_keys"
    elif command == "read_key":
        return "read_key"
    elif command == "pix_withdraw":
        return "pix_withdraw"
    return "fallback"


def build_graph(
    intent_service: IntentService,
    pix_key_service: PixKeyService,
    pix_withdraw_service: PixWithdrawService,
    response_service: ResponseService,
    logger,
    checkpointer=None,
):
    workflow = StateGraph(GraphState)

    workflow.add_node("identifyIntent", create_identify_intent_node(intent_service))
    workflow.add_node("listKeys", create_list_keys_node(pix_key_service))
    workflow.add_node("readKey", create_read_key_node(pix_key_service))
    workflow.add_node("pixWithdraw", create_pix_withdraw_node(pix_withdraw_service))
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("chatResponse", create_chat_response_node(response_service))

    workflow.add_edge(START, "identifyIntent")

    workflow.add_conditional_edges(
        "identifyIntent",
        route_intent,
        {
            "list_keys": "listKeys",
            "read_key": "readKey",
            "pix_withdraw": "pixWithdraw",
            "fallback": "fallback",
        },
    )

    workflow.add_edge("listKeys", "chatResponse")
    workflow.add_edge("readKey", "chatResponse")
    workflow.add_edge("pixWithdraw", "chatResponse")
    workflow.add_edge("fallback", "chatResponse")
    workflow.add_edge("chatResponse", END)

    return workflow.compile(checkpointer=checkpointer)
