"""TASK-13 — E2E telemetry: a graph run emits the expected domain spans.

Mocks only external/LLM boundaries (guardrail, intent, banking-backed services);
the domain spans themselves are produced by the real node code, so the test
fails if instrumentation regresses.
"""

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver


def _span_names(exporter):
    return {span.name for span in exporter.get_finished_spans()}


@pytest.mark.asyncio
async def test_chat_flow_emits_domain_spans(
    in_memory_spans, fake_checkpointer: MemorySaver
):
    from src.graph.factory import GraphProcessor

    with (
        patch(
            "src.services.guardrail_service.GuardrailService.check",
            new_callable=AsyncMock,
            return_value={"is_blocked": False},
        ),
        patch(
            "src.services.intent_service.IntentService.classify",
            new_callable=AsyncMock,
            return_value={"command": "list_keys"},
        ),
        patch(
            "src.services.pix_key_service.PixKeyService.list_keys",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "src.services.response_service.ResponseService.generate",
            new_callable=AsyncMock,
            return_value={"messages": [AIMessage(content="suas chaves: ...")]},
        ),
    ):
        graph = GraphProcessor(checkpointer=fake_checkpointer).get_graph()
        await graph.ainvoke(
            {"messages": [HumanMessage(content="listar minhas chaves pix")]},
            {"configurable": {"thread_id": "obs-e2e-1"}},
        )

    names = _span_names(in_memory_spans)
    assert "graph.guardrail.check" in names
    assert "graph.intent.identify" in names
    assert "pix.keys.list" in names
    assert "llm.response.generate" in names


@pytest.mark.asyncio
async def test_blocked_flow_skips_pix_spans(
    in_memory_spans, fake_checkpointer: MemorySaver
):
    from src.graph.factory import GraphProcessor

    with patch(
        "src.services.guardrail_service.GuardrailService.check",
        new_callable=AsyncMock,
        return_value={"is_blocked": True},
    ):
        graph = GraphProcessor(checkpointer=fake_checkpointer).get_graph()
        await graph.ainvoke(
            {"messages": [HumanMessage(content="conteudo malicioso")]},
            {"configurable": {"thread_id": "obs-e2e-2"}},
        )

    names = _span_names(in_memory_spans)
    assert "graph.guardrail.check" in names
    assert "pix.keys.list" not in names
