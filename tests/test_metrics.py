"""TASK-08 — domain metrics are recorded by domain_span and guardrail."""

from src.core.observability.domain import domain_span
from src.core.observability.domain_metrics import record_guardrail_block


def _metric_points(reader, name):
    data = reader.get_metrics_data()
    for resource_metric in data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == name:
                    return list(metric.data.data_points)
    return []


def test_node_duration_recorded(in_memory_metrics):
    with domain_span("pix.keys.list", **{"graph.node": "listKeys"}):
        pass

    points = _metric_points(in_memory_metrics, "graph_node_duration_seconds")
    assert points
    assert points[0].attributes["node"] == "listKeys"


def test_pix_operation_counter_increments(in_memory_metrics):
    with domain_span("pix.withdraw.execute", **{"graph.node": "pixWithdraw"}):
        pass

    points = _metric_points(in_memory_metrics, "pix_operations_total")
    assert points
    assert points[0].attributes["result"] == "ok"


def test_pix_operation_marks_error_on_failure(in_memory_metrics):
    try:
        with domain_span("pix.payment.execute", **{"graph.node": "pixPayment"}):
            raise RuntimeError("banking 5xx")
    except RuntimeError:
        pass

    points = _metric_points(in_memory_metrics, "pix_operations_total")
    assert points and points[0].attributes["result"] == "error"


def test_guardrail_block_counter(in_memory_metrics):
    record_guardrail_block(True)

    points = _metric_points(in_memory_metrics, "guardrail_block_total")
    assert points and points[0].attributes["result"] == "blocked"
