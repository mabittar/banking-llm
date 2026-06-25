"""TASK-04 — FastAPI root-span enrichment via the server request hook."""

from unittest.mock import MagicMock

from src.core.observability.fastapi_instrumentation import _server_request_hook


def _handler():  # pragma: no cover - used only for __qualname__/__module__
    return None


def test_hook_sets_route_method_and_handler():
    span = MagicMock()
    span.is_recording.return_value = True
    scope = {"path": "/chat", "method": "POST", "endpoint": _handler}
    route = MagicMock()
    route.path = "/chat"
    scope["route"] = route

    _server_request_hook(span, scope)

    span.update_name.assert_called_once_with("POST /chat")
    span.set_attribute.assert_any_call("http.route", "/chat")
    handler_calls = [
        c for c in span.set_attribute.call_args_list if c.args[0] == "app.handler"
    ]
    assert handler_calls and handler_calls[0].args[1].endswith("_handler")


def test_hook_noop_when_span_not_recording():
    span = MagicMock()
    span.is_recording.return_value = False

    _server_request_hook(span, {"path": "/chat", "method": "POST"})

    span.update_name.assert_not_called()
    span.set_attribute.assert_not_called()
