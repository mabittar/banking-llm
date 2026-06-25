"""Shared sensitive-data masking for logs, span attributes and metric labels.

Single source of truth so the privacy invariant (no full PIX key, government_id,
token or secret in any signal) is enforced identically across middleware logging
and telemetry attributes.
"""

from __future__ import annotations

from typing import Any

SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "authorization",
    "key",
    "api-key",
    "government_id",
    "jwt_secret",
    "transaction-hash-key",
}

_MASK = "********"


def mask_sensitive_data(data: Any) -> Any:
    """Recursively mask values under sensitive keys in dicts/lists."""
    if isinstance(data, dict):
        return {
            k: (_MASK if k.lower() in SENSITIVE_KEYS else mask_sensitive_data(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


def mask_pix_key(value: str) -> str:
    """Partially mask a PIX key, never exposing the full identifier.

    Examples: ``john@email.com`` -> ``***@email.com``; a phone/CPF -> last 4
    digits only.
    """
    if not value:
        return value
    if "@" in value:
        _, _, domain = value.partition("@")
        return f"***@{domain}"
    if len(value) <= 4:
        return _MASK
    return f"***{value[-4:]}"


def mask_attr(key: str, value: Any) -> Any:
    """Mask a span attribute / metric label value based on its key."""
    lowered = key.lower()
    if lowered in SENSITIVE_KEYS:
        return _MASK
    if "pix.key" in lowered or lowered.endswith("pix_key"):
        return mask_pix_key(str(value)) if value is not None else value
    return value


def mask_log_event(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """structlog processor enforcing the privacy invariant on every log signal.

    Applies the same masking used for spans/metrics so sensitive values never
    reach stdout, the OTLP log pipeline or Loki.
    """
    masked: dict[str, Any] = {}
    for key, value in event_dict.items():
        if isinstance(value, (dict, list)):
            masked[key] = mask_sensitive_data(value)
        else:
            masked[key] = mask_attr(key, value)
    return masked
