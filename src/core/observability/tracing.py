"""Tracer provider wiring.

Builds a TracerProvider with a batched OTLP span exporter. Kept independent from
the public API so ``telemetry.setup`` only orchestrates; no global side effects
happen on import.
"""

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from ..config import BaseSettings
from .exporters import is_http_protocol


def _build_span_exporter(settings: BaseSettings):
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
    if is_http_protocol(settings):
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        return OTLPSpanExporter(endpoint=endpoint)

    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    return OTLPSpanExporter(endpoint=endpoint, insecure=True)


def build_tracer_provider(settings: BaseSettings, resource: Resource) -> TracerProvider:
    """Create a TracerProvider with parent-based ratio sampling and OTLP export."""
    sampler = ParentBased(TraceIdRatioBased(settings.OTEL_TRACES_SAMPLER_ARG))
    provider = TracerProvider(resource=resource, sampler=sampler)
    provider.add_span_processor(BatchSpanProcessor(_build_span_exporter(settings)))
    return provider
