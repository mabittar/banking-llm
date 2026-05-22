from uuid import uuid4

from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from ..core.logger import logger
from ..graph.factory import GraphProcessor

chat_router = APIRouter(tags=["Chat"])


# ── Request / Response schemas ───────────────────────────────────────
class ChatRequest(BaseModel):
    """Payload sent by the client."""

    question: str = Field(
        ...,
        min_length=1,
        examples=["Quais são as chaves pix ativas da conta?"],
        description="The user's question to send to the LLM.",
    )
    thread_id: str | None = Field(
        None,
        description="Optional thread ID for multi-turn conversations. Omit for a one-shot conversation.",
    )


class ChatResponse(BaseModel):
    """Payload returned to the client."""

    answer: str


class ErrorResponse(BaseModel):
    """Payload returned to the client."""

    error: str


# ── Routes ───────────────────────────────────────────────────────────


@chat_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, raw_request: Request):
    try:
        cache = getattr(raw_request.app.state, "cache", None)
        checkpointer = getattr(raw_request.app.state, "checkpointer", None)
        thread_id = request.thread_id or str(uuid4())
        graph_processor = GraphProcessor(
            log=logger, cache_service=cache, checkpointer=checkpointer
        )
        graph = graph_processor.get_graph()
        config = {"configurable": {"thread_id": thread_id}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=request.question)]},
            config,
        )
        messages = result.get("messages", [])
        last_ai_message = messages[-1].content if messages else "Sem resposta."
        return ChatResponse(answer=last_ai_message)
    except Exception:
        logger.error("Error processing chat", exc_info=True)
        return ErrorResponse(error="Something went wrong. Please try again later.")
