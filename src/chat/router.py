from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from ..core.logger import logger
from ..graph.factory import GraphProcessor
from ..infrastructure.banking.banking_client import BankingClient
from ..infrastructure.llm_service import LLMService

chat_router = APIRouter(tags=["Chat"])


# ── Request / Response schemas ───────────────────────────────────────
class ChatRequest(BaseModel):
    """Payload sent by the client."""

    question: str = Field(
        ...,
        min_length=1,
        examples=["Quais são as chaves pix ativas da conta 550e8400?"],
        description="The user's question to send to the LLM.",
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
        llm_service = LLMService(logger)
        banking_client = BankingClient(logger, cache_service=cache)
        graph_processor = GraphProcessor(llm_service, banking_client, logger)
        graph = graph_processor.get_graph()
        result = await graph.ainvoke({"messages": [HumanMessage(content=request.question)]})
        messages = result.get("messages", [])
        last_ai_message = messages[-1].content if messages else "Sem resposta."
        return ChatResponse(answer=last_ai_message)
    except Exception:
        logger.error("Error calling LLM", exc_info=True)
        return ErrorResponse(error="Something went wrong. Please try again later.")
