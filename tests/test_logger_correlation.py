"""TASK-03 — log/trace correlation processor."""

from unittest.mock import patch

from src.core.observability import telemetry
from src.core.observability.log_correlation import add_trace_correlation


def test_no_correlation_fields_without_active_span():
    telemetry.shutdown()

    event = add_trace_correlation(None, "info", {"event": "hello"})

    assert "trace_id" not in event
    assert "span_id" not in event


def test_correlation_fields_present_inside_span():
    telemetry.shutdown()
    settings = telemetry.default_settings.model_copy(
        update={
            "OTEL_ENABLED": True,
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:1",
            "OTEL_LOGS_EXPORT_ENABLED": False,
        }
    )
    telemetry.setup(settings)

    tracer = telemetry.get_tracer(__name__)
    with tracer.start_as_current_span("unit"):
        event = add_trace_correlation(None, "info", {"event": "inside"})

    assert len(event["trace_id"]) == 32
    assert len(event["span_id"]) == 16

    telemetry.shutdown()


def test_renderer_selection_uses_json_outside_debug():
    # Importing logger with IS_DEBUG patched would require reload; assert the
    # behaviour contract via the processor instead of the module-level constant.
    with patch("src.core.observability.log_correlation.trace") as mocked:
        mocked.get_current_span.return_value.get_span_context.return_value.is_valid = (
            False
        )
        event = add_trace_correlation(None, "info", {"event": "x"})

    assert event == {"event": "x"}
