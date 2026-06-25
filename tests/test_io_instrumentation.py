"""TASK-05 — IO auto-instrumentation registers and uninstruments cleanly."""

from src.core.observability import telemetry


def _enabled_settings():
    return telemetry.default_settings.model_copy(
        update={
            "OTEL_ENABLED": True,
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:1",
            "OTEL_LOGS_EXPORT_ENABLED": False,
        }
    )


def test_io_instrumentors_registered_when_enabled():
    telemetry.shutdown()

    telemetry.setup(_enabled_settings())

    assert len(telemetry._state.instrumentors) >= 1

    telemetry.shutdown()
    assert telemetry._state.instrumentors == []


def test_no_instrumentors_when_disabled():
    telemetry.shutdown()

    telemetry.setup(
        telemetry.default_settings.model_copy(update={"OTEL_ENABLED": False})
    )

    assert telemetry._state.instrumentors == []
