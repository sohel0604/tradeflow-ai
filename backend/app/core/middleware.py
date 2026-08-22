"""
TradeFlow AI — Middleware
Day 16: Request logging + Correlation IDs

Every request gets:
1. A unique correlation ID (X-Correlation-ID header)
2. Structured log line: method, path, status, duration_ms
3. The correlation ID echoed back in the response header

Why correlation IDs?
When you have 100 log lines from 50 concurrent requests,
you need a way to trace ALL lines belonging to ONE request.
The correlation ID links them together.

Example log output:
  INFO  method=GET path=/health status=200 duration_ms=2.3 correlation_id=abc123
  INFO  method=POST path=/api/v1/auth/login status=200 duration_ms=145.2 correlation_id=def456
"""
import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request with:
    - correlation_id  → unique ID for this request (trace across logs)
    - method          → GET, POST, PUT, DELETE
    - path            → /api/v1/signals
    - status_code     → 200, 404, 500
    - duration_ms     → how long the request took
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # ------------------------------------------------------------------
        # 1. Get or generate correlation ID
        # If the client sent one (e.g. from another service), use it.
        # If not, generate a new UUID for this request.
        # ------------------------------------------------------------------
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4()),
        )

        # Bind to structlog context so ALL log lines in this request
        # automatically include the correlation_id
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id
        )

        # ------------------------------------------------------------------
        # 2. Time the request
        # ------------------------------------------------------------------
        start_time = time.perf_counter()

        # ------------------------------------------------------------------
        # 3. Process the request (call the actual route handler)
        # ------------------------------------------------------------------
        response = await call_next(request)

        # ------------------------------------------------------------------
        # 4. Calculate duration
        # ------------------------------------------------------------------
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # ------------------------------------------------------------------
        # 5. Log the completed request
        # Skip /health to avoid log spam from health check probes
        # ------------------------------------------------------------------
        if request.url.path not in ("/health", "/health/db"):
            logger.info(
                "request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        # ------------------------------------------------------------------
        # 6. Add correlation ID to response headers
        # Client can use this to report issues ("my request ID was abc123")
        # ------------------------------------------------------------------
        response.headers["X-Correlation-ID"] = correlation_id

        # Clear structlog context after request is done
        structlog.contextvars.unbind_contextvars("correlation_id")

        return response
