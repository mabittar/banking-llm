"""Domain metric instruments (RED-complementary, PIX, LLM, dependencies).

HTTP RED metrics are emitted by the FastAPI instrumentation; this module adds
the domain-specific counters/histograms from the SPEC. Instruments are created
lazily from the active meter and cached per meter-provider, so a toggle in tests
rebuilds them and a disabled pipeline yields no-op instruments.
"""

from __future__ import annotations

from typing import Any

from . import telemetry

_METER_NAME = "langchain-pix.domain"


class _DomainMetrics:
    def __init__(self, meter: Any) -> None:
        self.node_duration = meter.create_histogram(
            "graph_node_duration_seconds",
            unit="s",
            description="Duration of a LangGraph node execution.",
        )
        self.pix_operations = meter.create_counter(
            "pix_operations_total",
            description="PIX domain operations by intent and result.",
        )
        self.guardrail_blocks = meter.create_counter(
            "guardrail_block_total",
            description="Guardrail decisions by result.",
        )
        self.llm_tokens = meter.create_counter(
            "llm_token_count_total",
            description="LLM token usage by model.",
        )


_cache: dict[int, _DomainMetrics] = {}


def _instruments() -> _DomainMetrics:
    meter = telemetry.get_meter(_METER_NAME)
    key = id(meter)
    cached = _cache.get(key)
    if cached is None:
        cached = _DomainMetrics(meter)
        _cache[key] = cached
    return cached


def reset() -> None:
    """Clear the instrument cache (test isolation)."""
    _cache.clear()


def record_span_metrics(
    name: str, attributes: dict[str, Any], duration_s: float, error: bool
) -> None:
    """Record node duration and PIX operation outcome derived from a domain span."""
    instruments = _instruments()
    node = attributes.get("graph.node")
    if node:
        instruments.node_duration.record(
            duration_s, {"node": str(node), "error": str(error)}
        )

    if name.startswith("pix."):
        intent = str(attributes.get("pix.intent", name))
        result = "error" if error else "ok"
        instruments.pix_operations.add(1, {"intent": intent, "result": result})


def record_guardrail_block(blocked: bool) -> None:
    """Increment the guardrail decision counter."""
    _instruments().guardrail_blocks.add(
        1, {"result": "blocked" if blocked else "allowed"}
    )


def record_llm_tokens(model_name: str, count: int) -> None:
    """Increment the LLM tokens counter."""
    _instruments().llm_tokens.add(
        count, {"llm_model": model_name}
    )
