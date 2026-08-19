# Day 15 Notes — August 18, 2026
## Topic: FastAPI App Setup — Routing, Lifespan, Structure

---

## What is FastAPI?

FastAPI is a modern Python web framework.
It builds REST APIs — handles incoming HTTP requests
and returns JSON responses.

Why FastAPI over Flask or Django?
- **Speed**: one of the fastest Python frameworks (async I/O)
- **Auto docs**: generates Swagger UI at /docs automatically
- **Type safety**: uses Python type hints to validate data
- **Modern**: built for async — works perfectly with our async DB setup

---

## The folder structure we built today

```
backend/app/
├── main.py                  ← FastAPI app, registers all routers
├── core/
│   ├── config.py            ← settings from .env
│   └── database.py          ← DB connections
├── models/                  ← SQLAlchemy ORM models
└── api/
    └── v1/
        └── routes/
            ├── auth.py      ← /api/v1/auth/*
            ├── data.py      ← /api/v1/data/*
            ├── signals.py   ← /api/v1/signals/*
            ├── backtest.py  ← /api/v1/backtest/*
            ├── watchlist.py ← /api/v1/watchlist/*
            └── account.py   ← /api/v1/account/*
```

Why split routes into separate files?
- Each feature is isolated — auth changes don't touch signals code
- Multiple developers can work on different routes simultaneously
- Easy to find: "where is the signal endpoint?" → signals.py

Why `v1` in the path?
- API versioning — when we make breaking changes, we add `/v2`
- Old clients still use `/api/v1` — they keep working
- New clients use `/api/v2` — they get the new behavior

---

## APIRouter — route groups

```python
# In signals.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/status")
async def signals_status():
    return {"status": "ok"}
```

```python
# In main.py
from app.api.v1.routes import signals

app.include_router(
    signals.router,
    prefix="/api/v1/signals",
    tags=["signals"],
)
```

Result: `GET /api/v1/signals/status` → calls `signals_status()`

`prefix` adds the base path to ALL routes in the router.
`tags` groups routes together in Swagger UI at `/docs`.

---

## Lifespan — startup and shutdown

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP — runs before first request
    get_mongo_client()              # warm up connection
    os.makedirs(charts_dir)         # create charts folder

    yield                           # app runs here

    # SHUTDOWN — runs after last request
    await close_mongo_connection()  # clean up
```

The `yield` splits the function into two halves.
Everything BEFORE `yield` = startup code.
Everything AFTER `yield` = shutdown code.

Why warm up MongoDB on startup?
- First request would create the connection (50ms delay)
- Pre-warming means the first real user request is fast

Why close MongoDB on shutdown?
- Clean shutdown flushes any pending writes
- Prevents "connection reset" errors in the logs

---

## FastAPI auto-generates OpenAPI docs

FastAPI reads your route functions and type hints
and automatically generates:

- **Swagger UI** at `/docs` — interactive, try endpoints in browser
- **ReDoc** at `/redoc` — cleaner documentation view
- **OpenAPI JSON** at `/openapi.json` — machine-readable spec

This happens with zero extra code. Just define your routes
and the docs appear automatically.

The `tags=` parameter groups routes in the Swagger sidebar.
The docstring in each route function becomes the description.

---

## Route anatomy

```python
@app.get(          # HTTP method: GET, POST, PUT, DELETE, PATCH
    "/health",     # URL path
    tags=["health"],           # Swagger grouping
    summary="Basic health",    # Swagger title
)
async def health_check():      # async → non-blocking
    """Full description shown in Swagger docs."""
    return {"status": "ok"}   # FastAPI auto-converts dict to JSON
```

`async def` is critical — FastAPI is async by design.
A sync function would block the event loop while waiting for DB queries,
meaning NO other requests can be handled during that wait.
With `async def`, Python suspends the function and handles other requests.

---

## What we have at /docs right now

Open http://localhost:8000/docs and you'll see:

```
health
  GET /health          ← Basic health check
  GET /health/db       ← Database health check
  GET /               ← Root — API info

auth
  GET /api/v1/auth/status

data
  GET /api/v1/data/status

signals
  GET /api/v1/signals/status

backtest
  GET /api/v1/backtest/status

watchlist
  GET /api/v1/watchlist/status

account
  GET /api/v1/account/status
```

All routes are registered and clickable.
Stubs return simple JSON now.
We fill them in as we build each feature day by day.

---

## Tomorrow — Day 16
Add CORS middleware and request logging middleware.
Every request gets a unique correlation ID attached.
This makes debugging much easier — you can trace
a single request through all your log lines.
