"""Domain span helper.

``domain_span`` opens a span following the ``<layer>.<domain>.<operation>``
convention, masks sensitive attributes, always closes the span, and records
``ERROR`` status plus the exception on failure. It is a no-op-friendly wrapper:
when telemetry is disabled the OTel no-op tracer makes it virtually free.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from opentelemetry.trace import Status, StatusCode

from . import telemetry
from .domain_metrics import record_span_metrics
from .masking import mask_attr

if TYPE_CHECKING:
    from collections.abc import Iterator

_TRACER_NAME = "langchain-pix.domain"


@contextmanager
def domain_span(name: str, **attributes: Any) -> Iterator[Any]:
    """Open a domain span, masking attributes and recording failures + metrics."""
    tracer = telemetry.get_tracer(_TRACER_NAME)
    start = time.perf_counter()
    error = False
    with tracer.start_as_current_span(name) as span:
        _set_attributes(span, attributes)
        try:
            yield span
        except Exception as exc:
            error = True
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        finally:
            record_span_metrics(name, attributes, time.perf_counter() - start, error)


def _set_attributes(span: Any, attributes: dict[str, Any]) -> None:
    for key, value in attributes.items():
        if value is None:
            continue
        span.set_attribute(key, mask_attr(key, value))
