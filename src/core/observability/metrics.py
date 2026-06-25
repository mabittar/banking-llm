"""Meter provider wiring.

Builds a MeterProvider with a periodic OTLP metric reader (push model). The
application never exposes a ``/metrics`` endpoint; the Collector owns the
Prometheus exposition.
"""

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from ..config import BaseSettings
from .exporters import is_http_protocol


def _build_metric_exporter(settings: BaseSettings):
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
    if is_http_protocol(settings):
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )

        return OTLPMetricExporter(endpoint=endpoint)

    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )

    return OTLPMetricExporter(endpoint=endpoint, insecure=True)


def build_meter_provider(settings: BaseSettings, resource: Resource) -> MeterProvider:
    """Create a MeterProvider that pushes metrics to the Collector via OTLP."""
    reader = PeriodicExportingMetricReader(_build_metric_exporter(settings))
    return MeterProvider(resource=resource, metric_readers=[reader])
