"""TASK-07 — LLM instrumentation via OpenInference produces LLM spans."""

from itertools import cycle

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from openinference.instrumentation.langchain import LangChainInstrumentor

from src.core.observability import telemetry
from src.core.observability.instrumentation import instrument_llm


def test_instrument_llm_registers_langchain_instrumentor():
    instrumentors = instrument_llm()
    try:
        assert len(instrumentors) == 1
        assert isinstance(instrumentors[0], LangChainInstrumentor)
    finally:
        for instrumentor in instrumentors:
            instrumentor.uninstrument()


def test_llm_call_emits_span(in_memory_spans):
    instrumentor = LangChainInstrumentor()
    instrumentor.instrument(tracer_provider=telemetry._state.tracer_provider)
    try:
        model = GenericFakeChatModel(messages=cycle(["resposta de teste"]))
        model.invoke("qual a chave pix?")
    finally:
        instrumentor.uninstrument()

    spans = in_memory_spans.get_finished_spans()
    assert any(s.name for s in spans), "expected at least one LLM span"
