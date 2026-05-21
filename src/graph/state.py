from decimal import Decimal
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    output: str
    command: Literal["list_keys", "read_key", "pix_withdraw", "unknown"]
    pix_key: str | None
    action_success: bool | None
    action_error: str | None
    action_data: Any | None
    # Pix Withdraw fields
    withdraw_amount: Decimal | None
    withdraw_init_type: str | None
    withdraw_beneficiary: dict | None
    withdraw_end_to_end_id: str | None
    withdraw_additional_info: str | None
    withdraw_qr_code: str | None
    withdraw_reconciliation_id: str | None
    withdraw_key_id: str | None
    withdraw_amount_type: str | None
    withdraw_nominal_amount: Decimal | None
