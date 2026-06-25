import logging

import structlog

from .config import settings
from .observability.log_correlation import add_trace_correlation
from .observability.masking import mask_log_event

# JSON outside dev so the OTLP log pipeline and Loki get structured records;
# the human-friendly ConsoleRenderer stays for local debugging.
_renderer = (
    structlog.dev.ConsoleRenderer()
    if settings.IS_DEBUG
    else structlog.processors.JSONRenderer()
)

# Processors shared by structlog-native and stdlib ("foreign") records so every
# log line carries the same masking, timestamp and trace correlation.
_shared_processors = [
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    mask_log_event,
    add_trace_correlation,
]

# Route structlog through the stdlib logging tree so the OpenTelemetry handler
# (attached by observability.setup) can export application logs over OTLP.
structlog.configure(
    processors=[
        *_shared_processors,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

_formatter = structlog.stdlib.ProcessorFormatter(
    processors=[
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        _renderer,
    ],
    foreign_pre_chain=_shared_processors,
)

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)

_root_logger = logging.getLogger()
if not any(isinstance(h, logging.StreamHandler) for h in _root_logger.handlers):
    _root_logger.addHandler(_stream_handler)
_root_logger.setLevel(logging.INFO)


logger = structlog.get_logger(__name__)
