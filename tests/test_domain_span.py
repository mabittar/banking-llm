"""TASK-06 — domain_span produces masked spans and records failures."""

import pytest

from src.core.observability.domain import domain_span


def test_domain_span_records_masked_attributes(in_memory_spans):
    with domain_span(
        "pix.withdraw.execute",
        **{"graph.node": "pixWithdraw", "pix.key.masked": "john@email.com"},
    ):
        pass

    spans = in_memory_spans.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "pix.withdraw.execute"
    assert span.attributes["graph.node"] == "pixWithdraw"
    assert span.attributes["pix.key.masked"] == "***@email.com"
    assert "john@email.com" not in str(span.attributes)


def test_domain_span_marks_error_on_exception(in_memory_spans):
    with pytest.raises(ValueError):
        with domain_span("pix.payment.execute", **{"graph.node": "pixPayment"}):
            raise ValueError("banking 5xx")

    span = in_memory_spans.get_finished_spans()[0]
    assert span.status.status_code.name == "ERROR"
    assert span.events  # exception recorded
