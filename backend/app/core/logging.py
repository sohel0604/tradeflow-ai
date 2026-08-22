"""
TradeFlow AI — Structured Logging
Day 16: JSON logs in production, pretty logs in development.

Why structured (JSON) logs?
- Every log line is a valid JSON object
- Log aggregators (Datadog, CloudWatch) can parse and search them
- You can filter: "show all requests with status_code=500"
- Correlation IDs link related log lines across services

Example production log line:
{
  "timestamp": "2026-08-16T06:30:01.234Z",
  "level": "info",
  "service": "tradeflow-api",
  "correlation_id": "abc-123",
  "event": "request",
  "method": "GET",
  "path": "/api/v1/signals",
  "status_code": 200,
  "duration_ms": 42.3
}
"""
import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure structlog for structured logging.
    Call this ONCE at application startup (in main.py).

    Development: pretty coloured output for readability
    Production:  JSON output for log aggregators
    """

    # Processors run on every log line in order
    # Each processor receives the log record and can modify or format it
    shared_processors = [
        # Merge any bound context variables (like correlation_id)
        structlog.contextvars.merge_contextvars,

        # Add the logger name (e.g. "app.core.middleware")
        structlog.stdlib.add_logger_name,

        # Add log level (info, warning, error)
        structlog.stdlib.add_log_level,

        # Add ISO timestamp
        structlog.processors.TimeStamper(fmt="iso"),

        # Add service name to every log line
        structlog.processors.CallsiteParameterAdder(
            [structlog.processors.CallsiteParameter.FUNC_NAME]
        ),
    ]

    if settings.app_env == "development":
        # Pretty coloured output — easier to read in terminal
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON output — parseable by log aggregators
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    # Apply to root logger so ALL Python logging goes through structlog
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    )

    # Suppress noisy third-party loggers
    for noisy_logger in [
        "uvicorn.access",     # uvicorn prints its own access log — we handle it
        "sqlalchemy.engine",  # SQL queries are verbose — only enable for debugging
        "httpx",              # HTTP client debug info
        "watchfiles",         # file watcher notifications
    ]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
