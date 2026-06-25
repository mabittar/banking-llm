"""structlog processor that correlates log lines with the active OTel span.

When a valid span is in context, ``add_trace_correlation`` enriches the event
dict with ``trace_id``/``span_id`` (hex, matching the format used by Tempo and
the OTLP log exporter). Without an active span it is a pure pass-through, so logs
outside a request keep their current shape.
"""

from __future__ import annotations

from typing import Any

from opentelemetry import trace

EventDict = dict[str, Any]


def add_trace_correlation(
    _logger: Any, _method: str, event_dict: EventDict
) -> EventDict:
    """Attach trace_id/span_id to the log event when a span is recording."""
    span = trace.get_current_span()
    context = span.get_span_context()
    if not context.is_valid:
        return event_dict

    event_dict["trace_id"] = trace.format_trace_id(context.trace_id)
    event_dict["span_id"] = trace.format_span_id(context.span_id)
    return event_dict
