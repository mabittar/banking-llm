"""OTLP exporter selection shared by traces, metrics and logs.

Centralises the gRPC/HTTP protocol decision so each signal builder stays small
and the protocol is resolved in a single place.
"""

from ..config import BaseSettings

_HTTP_PROTOCOLS = {"http", "http/protobuf", "httpprotobuf"}


def is_http_protocol(settings: BaseSettings) -> bool:
    """Return True when OTLP should use the HTTP/protobuf transport."""
    return settings.OTEL_EXPORTER_OTLP_PROTOCOL.lower() in _HTTP_PROTOCOLS
