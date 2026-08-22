# Day 17 Notes — August 20, 2026
## Topic: pydantic-settings Config + /config-check Dev Route

---

## What is pydantic-settings?

`pydantic-settings` reads environment variables from `.env`
and validates them as typed Python attributes.

Without it — manual, error-prone:
```python
import os
db_host = os.getenv("POSTGRES_HOST", "postgres")  # returns str or None
debug = os.getenv("DEBUG", "false") == "true"      # manual bool conversion
port = int(os.getenv("POSTGRES_PORT", "5432"))     # manual int conversion
```

With pydantic-settings — automatic, type-safe:
```python
class Settings(BaseSettings):
    postgres_host: str = "postgres"
    debug: bool = True           # automatically converts "true" → True
    postgres_port: int = 5432    # automatically converts "5432" → 5432
```

Pydantic reads `POSTGRES_HOST` from the environment,
validates it matches `str`, and assigns it to `settings.postgres_host`.

---

## @lru_cache — why it matters

```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()  # called at module import time
```

`@lru_cache` = Least Recently Used cache.
The first call creates a `Settings()` object.
Every subsequent call returns the SAME cached object.

Without `@lru_cache`:
```python
# Every import of settings creates a new Settings() object
# Settings() reads .env every time → slow
# You'd have 100 Settings objects if 100 modules import it
```

With `@lru_cache`:
```python
# .env is read ONCE at startup
# All 100 modules share the SAME Settings object
# Zero overhead after the first call
```

---

## The /config-check endpoint — what it shows

```
GET /api/v1/dev/config-check
```

Returns a safe view of current configuration:

```json
{
  "app_env": "development",
  "debug": true,
  "log_level": "INFO",
  "allowed_origins": ["http://localhost:3000", "http://localhost:5173"],
  "postgres_host": "postgres",
  "postgres_port": 5432,
  "postgres_db": "tradeflow",
  "postgres_user": "tradeflow",
  "postgres_password": "***hidden***",

  "api_keys_configured": {
    "anthropic": false,
    "sendgrid": false,
    "telegram": false,
    "stripe": false,
    "razorpay": false,
    "aws": false,
    "dhan": false
  }
}
```

The `api_keys_configured` section is brilliant:
- Shows `true` or `false` whether the key is set
- NEVER shows the actual key value
- Tells you instantly which integrations are ready

Production safety:
```python
if settings.app_env != "development":
    raise HTTPException(status_code=404)
    # Returns 404 in production — endpoint doesn't "exist"
```

---

## How main.py is structured after Day 17

```python
# 1. Configure logging FIRST (before anything else logs)
configure_logging()

# 2. Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# 3. Add middleware (last added = first to run)
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(RequestLoggingMiddleware)

# 4. Register exception handlers
app.add_exception_handler(TradeFlowException, ...)
app.add_exception_handler(StarletteHTTPException, ...)
app.add_exception_handler(RequestValidationError, ...)
app.add_exception_handler(Exception, ...)  # catch-all

# 5. Register routes
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(data.router, prefix="/api/v1/data")
# ... etc
```

This is the final structure. Every future feature just adds
a new router file and one `include_router()` line here.

---

## What every request looks like now

```
1. Request arrives: GET /api/v1/signals/status

2. RequestLoggingMiddleware:
   - generates correlation_id = "abc-123"
   - binds to structlog context
   - starts timer

3. CORSMiddleware:
   - checks origin header
   - adds CORS response headers

4. Route handler runs:
   - returns {"router": "signals", "status": "coming Day 88"}

5. CORSMiddleware finishes

6. RequestLoggingMiddleware finishes:
   - logs: method=GET path=/api/v1/signals/status status=200 duration_ms=1.2
   - adds X-Correlation-ID: abc-123 to response headers

7. Response sent to client with X-Correlation-ID header
```

---

## Files built across Days 16-17

```
backend/app/
├── main.py                         ← updated: CORS + middleware + exception handlers + logging
├── core/
│   ├── middleware.py               ← RequestLoggingMiddleware + correlation IDs
│   ├── logging.py                  ← structlog configuration
│   └── exceptions.py               ← 4 exception types + 4 global handlers
└── api/v1/routes/
    └── config.py                   ← /api/v1/dev/config-check (dev only)
```

---

## Tomorrow — Day 18
Pydantic v2 schemas.
We write typed request/response models that FastAPI uses
to validate incoming data and serialise outgoing data.
This is what makes FastAPI so much safer than raw Flask.
