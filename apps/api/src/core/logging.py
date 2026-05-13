"""Structured logging configuration using structlog.

Configures structlog with JSON output for production and
pretty console output for development.
"""
import logging
import sys

import structlog


def configure_logging(*, debug: bool = False) -> None:
    """Configure structlog for the application.

    Uses stdlib LoggerFactory so add_logger_name works correctly.

    Args:
        debug: If True, use pretty console output. Otherwise use JSON.
    """
    level = logging.DEBUG if debug else logging.INFO

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if debug:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure the stdlib root logger so output reaches stdout.
    handler = logging.StreamHandler(sys.stdout)
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)
