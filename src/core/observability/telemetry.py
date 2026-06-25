"""Telemetry bootstrap.

Single entry point that wires the three OTel signals (traces, metrics, logs) and
the runtime instrumentations. Designed to be a strict no-op while
``settings.OTEL_ENABLED`` is false: no provider, exporter or network dependency
is created, so the application behaves exactly as before.

Export failures (e.g. Collector offline) are intentionally swallowed at the
batch-processor level by the OTel SDK and never propagate to the request path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog
from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource

from ..config import BaseSettings
from ..config import settings as default_settings

# Use structlog directly (not core.logger) to avoid an import cycle:
# core.logger -> observability package -> telemetry -> core.logger.
logger = structlog.get_logger(__name__)


@dataclass
class _TelemetryState:
    enabled: bool = False
    tracer_provider: Any = None
    meter_provider: Any = None
    logger_provider: Any = None
    instrumentors: list[Any] = field(default_factory=list)


_state = _TelemetryState()


def is_enabled() -> bool:
    """Return whether telemetry providers are currently active."""
    return _state.enabled


def _build_resource(settings: BaseSettings) -> Resource:
    return Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": getattr(settings, "version", "0.1.0"),
            "deployment.environment": str(getattr(settings, "ENVIRONMENT", "local")),
        }
    )


def setup(settings: BaseSettings | None = None) -> None:
    """Bootstrap telemetry. No-op when OTEL_ENABLED is false or already set up."""
    settings = settings or default_settings
    if not settings.OTEL_ENABLED:
        logger.debug("Telemetry disabled (OTEL_ENABLED=false); skipping setup")
        return
    if _state.enabled:
        return

    resource = _build_resource(settings)
    _setup_tracing(settings, resource)
    _setup_metrics(settings, resource)
    _setup_logs(settings, resource)
    _register_instrumentations(settings)

    _state.enabled = True
    logger.info(
        "Telemetry enabled",
        service=settings.OTEL_SERVICE_NAME,
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        protocol=settings.OTEL_EXPORTER_OTLP_PROTOCOL,
    )


def _setup_tracing(settings: BaseSettings, resource: Resource) -> None:
    from .tracing import build_tracer_provider

    _state.tracer_provider = build_tracer_provider(settings, resource)
    trace.set_tracer_provider(_state.tracer_provider)


def _setup_metrics(settings: BaseSettings, resource: Resource) -> None:
    if not settings.OTEL_METRICS_ENABLED:
        return
    from .metrics import build_meter_provider

    _state.meter_provider = build_meter_provider(settings, resource)
    metrics.set_meter_provider(_state.meter_provider)


def _setup_logs(settings: BaseSettings, resource: Resource) -> None:
    if not settings.OTEL_LOGS_EXPORT_ENABLED:
        return
    from .logging_export import attach_logging_handler, build_logger_provider

    _state.logger_provider = build_logger_provider(settings, resource)
    attach_logging_handler(_state.logger_provider)


def _register_instrumentations(settings: BaseSettings) -> None:
    """Register runtime instrumentations (IO + LLM via OpenInference)."""
    from .instrumentation import instrument_io, instrument_llm

    _state.instrumentors.extend(instrument_io())
    _state.instrumentors.extend(instrument_llm())


def get_tracer(name: str) -> trace.Tracer:
    """Return a tracer. Prefers the local provider; falls back to the no-op API."""
    if _state.tracer_provider is not None:
        return _state.tracer_provider.get_tracer(name)
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Return a meter. Prefers the local provider; falls back to the no-op API."""
    if _state.meter_provider is not None:
        return _state.meter_provider.get_meter(name)
    return metrics.get_meter(name)


def shutdown() -> None:
    """Tear down providers and instrumentors. Safe to call when disabled."""
    for instrumentor in _state.instrumentors:
        try:
            instrumentor.uninstrument()
        except Exception:  # noqa: BLE001 - teardown must never raise
            logger.debug(
                "Instrumentor uninstrument failed", instrumentor=str(instrumentor)
            )
    _state.instrumentors.clear()

    for provider in (
        _state.tracer_provider,
        _state.meter_provider,
        _state.logger_provider,
    ):
        shutdown_fn = getattr(provider, "shutdown", None)
        if shutdown_fn:
            shutdown_fn()

    _state.tracer_provider = None
    _state.meter_provider = None
    _state.logger_provider = None
    _state.enabled = False
