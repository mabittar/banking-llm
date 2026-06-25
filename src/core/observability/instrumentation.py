"""Runtime IO and LLM instrumentations.

Each registrar is best-effort and tolerant: a missing optional package or an
instrumentation error is logged and skipped, never raised, so telemetry setup
cannot break application start. Instrumentors are returned so ``telemetry`` can
uninstrument them on shutdown (important for test isolation).
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def _safe_instrument(factory) -> Any | None:
    try:
        instrumentor = factory()
        instrumentor.instrument()
        return instrumentor
    except Exception as exc:  # noqa: BLE001 - instrumentation must not break boot
        logger.warning("Instrumentation skipped", error=str(exc))
        return None


def instrument_io() -> list[Any]:
    """Instrument outbound IO: HTTP (requests), Redis and PostgreSQL (psycopg)."""
    factories = []

    def _requests():
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        return RequestsInstrumentor()

    def _redis():
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        return RedisInstrumentor()

    def _psycopg():
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

        return PsycopgInstrumentor()

    factories.extend([_requests, _redis, _psycopg])
    return [i for i in (_safe_instrument(f) for f in factories) if i is not None]


def instrument_llm() -> list[Any]:
    """Instrument LangChain/LLM calls via OpenInference (GenAI semantics)."""

    def _langchain():
        from openinference.instrumentation.langchain import LangChainInstrumentor

        return LangChainInstrumentor()

    instrumentor = _safe_instrument(_langchain)
    return [instrumentor] if instrumentor is not None else []
