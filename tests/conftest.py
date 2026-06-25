import pytest
from langgraph.checkpoint.memory import MemorySaver
from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from src.core.observability import domain_metrics, telemetry
from tests import FakeCache


@pytest.fixture
def fake_cache() -> FakeCache:
    return FakeCache()


@pytest.fixture
def fake_checkpointer() -> MemorySaver:
    return MemorySaver()


@pytest.fixture
def in_memory_spans() -> InMemorySpanExporter:
    """Activate telemetry with an in-memory span exporter for assertions.

    Avoids any network exporter; tears the global provider down afterwards so
    tests stay isolated and repeatable.
    """
    telemetry.shutdown()
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    telemetry._state.tracer_provider = provider
    telemetry._state.enabled = True
    trace.set_tracer_provider(provider)
    yield exporter
    telemetry.shutdown()


@pytest.fixture
def in_memory_metrics() -> InMemoryMetricReader:
    """Activate telemetry metrics with an in-memory reader for assertions."""
    telemetry.shutdown()
    domain_metrics.reset()
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    telemetry._state.meter_provider = provider
    telemetry._state.enabled = True
    yield reader
    domain_metrics.reset()
    telemetry.shutdown()
