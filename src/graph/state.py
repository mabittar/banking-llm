from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    output: str
    command: Literal["list_keys", "read_key", "unknown"]
    pix_key: str | None
    action_success: bool | None
    action_error: str | None
    action_data: Any | None
