"""Logs provider wiring (OTel Logs SDK over OTLP).

Bridges Python's stdlib logging (the sink structlog forwards to) into the OTel
log pipeline, so logs reach the Collector via OTLP — no Promtail/Alloy agent.
"""

import logging

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from ..config import BaseSettings
from .exporters import is_http_protocol


def _build_log_exporter(settings: BaseSettings):
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
    if is_http_protocol(settings):
        from opentelemetry.exporter.otlp.proto.http._log_exporter import (
            OTLPLogExporter,
        )

        return OTLPLogExporter(endpoint=endpoint)

    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

    return OTLPLogExporter(endpoint=endpoint, insecure=True)


def build_logger_provider(settings: BaseSettings, resource: Resource) -> LoggerProvider:
    """Create a LoggerProvider that batches log records to the Collector."""
    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(
        BatchLogRecordProcessor(_build_log_exporter(settings))
    )
    return provider


def attach_logging_handler(provider: LoggerProvider) -> LoggingHandler:
    """Attach an OTLP handler to the root stdlib logger and return it."""
    handler = LoggingHandler(level=logging.INFO, logger_provider=provider)
    logging.getLogger().addHandler(handler)
    return handler
