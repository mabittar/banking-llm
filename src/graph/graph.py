from langgraph.graph import END, START, StateGraph

from ..infrastructure.banking_client import BankingClient
from ..infrastructure.llm_service import LLMService
from .nodes.chat_response_node import create_chat_response_node
from .nodes.fallback_node import fallback_node
from .nodes.identify_intent import create_identify_intent_node
from .nodes.list_keys_node import create_list_keys_node
from .nodes.read_key_node import create_read_key_node
from .state import GraphState


def route_intent(state: GraphState) -> str:
    command = state.get("command", "unknown")
    if command == "list_keys":
        return "list_keys"
    elif command == "read_key":
        return "read_key"
    return "fallback"


def build_graph(llm_service: LLMService, banking_client: BankingClient, logger):
    workflow = StateGraph(GraphState)

    workflow.add_node("identifyIntent", create_identify_intent_node(llm_service))
    workflow.add_node("listKeys", create_list_keys_node(logger, banking_client))
    workflow.add_node("readKey", create_read_key_node(logger, banking_client))
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("chatResponse", create_chat_response_node(llm_service))

    workflow.add_edge(START, "identifyIntent")

    workflow.add_conditional_edges(
        "identifyIntent",
        route_intent,
        {
            "list_keys": "listKeys",
            "read_key": "readKey",
            "fallback": "fallback",
        },
    )

    workflow.add_edge("listKeys", "chatResponse")
    workflow.add_edge("readKey", "chatResponse")
    workflow.add_edge("fallback", "chatResponse")
    workflow.add_edge("chatResponse", END)

    return workflow.compile()
