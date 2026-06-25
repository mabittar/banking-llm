"""FastAPI instrumentation and root-span enrichment.

Wraps the ASGI app with OTel's FastAPI instrumentor and, via a server request
hook, enriches the root SERVER span with a readable route name plus the
``app.handler`` attribute. No-op unless telemetry is enabled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import telemetry

if TYPE_CHECKING:
    from opentelemetry.trace import Span


def _server_request_hook(span: Span, scope: dict[str, Any]) -> None:
    if not span or not span.is_recording():
        return

    route = scope.get("route")
    route_path = getattr(route, "path", None) or scope.get("path", "")
    method = scope.get("method", "")
    if route_path:
        span.set_attribute("http.route", route_path)
    if method and route_path:
        span.update_name(f"{method} {route_path}")

    endpoint = scope.get("endpoint")
    if endpoint is not None:
        handler = f"{endpoint.__module__}.{endpoint.__qualname__}"
        span.set_attribute("app.handler", handler)


def instrument_fastapi_app(app: Any) -> None:
    """Instrument a FastAPI app instance when telemetry is enabled."""
    if not telemetry.is_enabled():
        return

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app, server_request_hook=_server_request_hook)
