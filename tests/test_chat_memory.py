from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture(autouse=True)
def disable_guardrail():
    with patch(
        "src.services.guardrail_service.GuardrailService.check",
        new_callable=AsyncMock,
        return_value={"is_blocked": False},
    ):
        yield


@pytest.mark.asyncio
async def test_graph_accepts_checkpointer(fake_checkpointer: MemorySaver):
    from src.graph.factory import GraphProcessor

    processor = GraphProcessor(checkpointer=fake_checkpointer)
    graph = processor.get_graph()
    assert graph.checkpointer is fake_checkpointer


@pytest.mark.asyncio
async def test_same_thread_accumulates_messages(fake_checkpointer: MemorySaver):
    from src.graph.factory import GraphProcessor

    processor = GraphProcessor(checkpointer=fake_checkpointer)
    graph = processor.get_graph()

    first = await graph.ainvoke(
        {"messages": [HumanMessage(content="listar chaves da conta 550e8400")]},
        {"configurable": {"thread_id": "test-thread-1"}},
    )
    first_count = len(first.get("messages", []))

    second = await graph.ainvoke(
        {"messages": [HumanMessage(content="qual meu nome?")]},
        {"configurable": {"thread_id": "test-thread-1"}},
    )
    second_count = len(second.get("messages", []))

    assert (
        second_count > first_count
    ), f"Expected more messages after second invoke ({second_count} > {first_count})"


@pytest.mark.asyncio
async def test_different_threads_isolated(fake_checkpointer: MemorySaver):
    from src.graph.factory import GraphProcessor

    processor = GraphProcessor(checkpointer=fake_checkpointer)
    graph = processor.get_graph()

    a = await graph.ainvoke(
        {"messages": [HumanMessage(content="ola, sou o Joao")]},
        {"configurable": {"thread_id": "thread-a"}},
    )
    b = await graph.ainvoke(
        {"messages": [HumanMessage(content="ola, sou a Maria")]},
        {"configurable": {"thread_id": "thread-b"}},
    )

    a_messages = [m for m in a.get("messages", []) if isinstance(m, HumanMessage)]
    b_messages = [m for m in b.get("messages", []) if isinstance(m, HumanMessage)]

    a_text = " ".join(m.content for m in a_messages)
    b_text = " ".join(m.content for m in b_messages)

    assert "Joao" in a_text
    assert "Maria" not in a_text
    assert "Maria" in b_text
    assert "Joao" not in b_text


@pytest.mark.asyncio
async def test_without_checkpointer_still_works():
    from src.graph.factory import GraphProcessor

    processor = GraphProcessor()
    graph = processor.get_graph()

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="ola")]},
        {"configurable": {"thread_id": str(uuid4())}},
    )
    messages = result.get("messages", [])
    last = messages[-1] if messages else None
    assert last is not None
    assert isinstance(last, AIMessage)


@pytest.mark.asyncio
async def test_no_thread_id_uses_generated_uuid(fake_checkpointer: MemorySaver):
    from src.graph.factory import GraphProcessor

    processor = GraphProcessor(checkpointer=fake_checkpointer)
    graph = processor.get_graph()

    tid = str(uuid4())
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="ola")]},
        {"configurable": {"thread_id": tid}},
    )
    messages = result.get("messages", [])
    assert len(messages) > 0
