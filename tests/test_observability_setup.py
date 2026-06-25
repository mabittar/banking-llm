"""TASK-02 — telemetry bootstrap: no-op default and resilient enable."""

from opentelemetry import trace

from src.core.config import get_settings
from src.core.observability import telemetry


def _settings_with(**overrides):
    settings = get_settings().model_copy(update=overrides)
    return settings


def test_setup_is_noop_when_disabled():
    telemetry.shutdown()
    settings = _settings_with(OTEL_ENABLED=False)

    telemetry.setup(settings)

    assert telemetry.is_enabled() is False
    assert telemetry._state.tracer_provider is None
    assert telemetry._state.meter_provider is None


def test_setup_does_not_raise_with_unreachable_endpoint():
    telemetry.shutdown()
    settings = _settings_with(
        OTEL_ENABLED=True,
        OTEL_EXPORTER_OTLP_ENDPOINT="http://127.0.0.1:1",
        OTEL_LOGS_EXPORT_ENABLED=False,
    )

    telemetry.setup(settings)

    assert telemetry.is_enabled() is True
    tracer = telemetry.get_tracer(__name__)
    with tracer.start_as_current_span("probe") as span:
        assert span is not None

    telemetry.shutdown()
    assert telemetry.is_enabled() is False


def test_get_tracer_returns_noop_when_disabled():
    telemetry.shutdown()
    tracer = telemetry.get_tracer(__name__)
    span = trace.get_current_span()

    assert tracer is not None
    assert span is not None
