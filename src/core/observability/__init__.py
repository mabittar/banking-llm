"""Observability package.

Public API for telemetry bootstrap and domain instrumentation helpers. Importing
this package has no side effects; call ``setup`` explicitly during app start.
"""

from .domain import domain_span
from .telemetry import get_meter, get_tracer, is_enabled, setup, shutdown

__all__ = [
    "setup",
    "shutdown",
    "get_tracer",
    "get_meter",
    "is_enabled",
    "domain_span",
]
