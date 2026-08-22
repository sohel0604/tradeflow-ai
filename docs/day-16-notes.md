# Day 16 Notes — August 19, 2026
## Topic: CORS, Request Logging Middleware, Correlation IDs, Exception Handlers

---

## What is Middleware?

Middleware wraps every request like an onion.
Every incoming request passes THROUGH middleware BEFORE hitting your route.
Every outgoing response passes THROUGH middleware AFTER your route.

```
Incoming request
      ↓
RequestLoggingMiddleware.dispatch() starts
      ↓
CORSMiddleware.dispatch() starts
      ↓
Your route handler runs
      ↓
CORSMiddleware.dispatch() finishes (adds CORS headers)
      ↓
RequestLoggingMiddleware.dispatch() finishes (logs the result)
      ↓
Outgoing response
```

Order matters — the LAST middleware added wraps OUTERMOST.

---

## CORS — why browsers need it

CORS = Cross-Origin Resource Sharing.

Your React frontend runs at `http://localhost:3000`.
Your FastAPI runs at `http://localhost:8000`.

They are different origins (different port = different origin).
Browsers BLOCK cross-origin requests by default for security.

Without CORS config:
```
Browser: "I want to fetch from localhost:8000"
Browser: *blocks the request before it even sends*
Error: "Access-Control-Allow-Origin header missing"
```

With CORS config:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

FastAPI adds the `Access-Control-Allow-Origin` header to responses.
Browser sees the header → allows the request.

In production: `allow_origins=["https://app.tradeflow.ai"]`
NEVER use `allow_origins=["*"]` in production with `allow_credentials=True`
— it's a security vulnerability.

---

## Correlation IDs — tracing requests

Problem: you have 100 log lines from 50 concurrent requests.
Which log lines belong to which request?

Solution: every request gets a unique ID.
Every log line in that request includes that ID.

```python
correlation_id = str(uuid.uuid4())
# e.g. "f47ac10b-58cc-4372-a567-0e02b2c3d479"

structlog.contextvars.bind_contextvars(
    correlation_id=correlation_id
)
```

Now every `logger.info(...)` call anywhere in that request
automatically includes `correlation_id=f47ac10b-...`.

```
# Request 1 logs
INFO  correlation_id=abc  path=/signals  duration_ms=42
INFO  correlation_id=abc  db_query=SELECT...  rows=20
INFO  correlation_id=abc  cache_hit=True

# Request 2 logs (interleaved, but distinguishable)
INFO  correlation_id=xyz  path=/health  duration_ms=1
```

Filter by correlation_id → see ALL lines from ONE request.
This is called "distributed tracing" at the log level.

We also echo the correlation ID back in the response header:
```
response.headers["X-Correlation-ID"] = correlation_id
```

If a user reports "my request failed", they can share the ID
and you can find every log line for that exact request.

---

## RequestLoggingMiddleware — what it does

```python
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 1. Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # 2. Bind to structlog context (all logs in this request get it)
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # 3. Start timer
        start = time.perf_counter()

        # 4. Run the actual route handler
        response = await call_next(request)

        # 5. Calculate duration
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # 6. Log the result
        logger.info("request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # 7. Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id

        # 8. Clean up context
        structlog.contextvars.unbind_contextvars("correlation_id")

        return response
```

We skip logging `/health` and `/health/db` — Kubernetes probes
hit these every 10 seconds and would flood your logs.

---

## Exception Handlers — the 4 layers

```
TradeFlowException     ← our custom errors (controlled, expected)
      ↓ if not caught
StarletteHTTPException ← FastAPI 404, 403 etc.
      ↓ if not caught
RequestValidationError ← Pydantic validation failures
      ↓ if not caught
Exception              ← anything else → 500, clean JSON
```

The golden rule: **never expose stack traces to users**.

```python
# BAD — exposes internal code paths
return JSONResponse(500, {"error": str(exc), "traceback": traceback.format_exc()})

# GOOD — user gets clean message, logs get full detail
logger.error("unhandled", error=str(exc), exc_info=True)  # full trace in logs
return JSONResponse(500, {"error": "Internal server error"})
```

---

## Structured logging — dev vs prod

```python
if settings.app_env == "development":
    renderer = structlog.dev.ConsoleRenderer(colors=True)
    # Pretty coloured output:
    # 2026-08-19 [info     ] request  method=GET path=/health status=200

else:
    renderer = structlog.processors.JSONRenderer()
    # Machine-readable JSON:
    # {"timestamp":"2026-08-19T...","level":"info","event":"request","method":"GET",...}
```

Development: human readable → easier to debug
Production: JSON → parseable by Datadog, CloudWatch, Grafana Loki

---

## Files built today

```
backend/app/core/
├── middleware.py   ← RequestLoggingMiddleware + correlation IDs
├── logging.py      ← structlog configuration
└── exceptions.py   ← custom exceptions + 4 global handlers
```
