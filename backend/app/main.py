"""
TradeFlow AI — FastAPI Application
Day 15: Properly structured app with all route groups registered.

Structure:
  app = FastAPI(lifespan=lifespan)
    ↓
  Middleware (added Day 16 onwards)
    ↓
  Route groups:
    /api/v1/auth      ← JWT register/login (Day 79)
    /api/v1/data      ← price bars, CSV upload (Day 28)
    /api/v1/signals   ← AI signals (Day 88)
    /api/v1/backtest  ← strategy results (Day 91)
    /api/v1/watchlist ← user symbols (Day 89)
    /api/v1/account   ← profile, billing, keys (Day 95)
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal,
    close_mongo_connection,
    get_mongo_client,
)

# ---------------------------------------------------------------------------
# Route routers — each feature group is its own module
# ---------------------------------------------------------------------------
from app.api.v1.routes import (
    auth,
    data,
    signals,
    backtest,
    watchlist,
    account,
)


# =============================================================================
# Lifespan — runs BEFORE first request and AFTER last request
# Use this for: DB connection warmup, background task startup, cleanup
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- STARTUP ----
    # Warm up MongoDB connection pool
    # First request won't be slow from a cold connection
    get_mongo_client()

    # Create charts directory if it doesn't exist
    os.makedirs(settings.charts_dir, exist_ok=True)

    yield  # ← app runs and handles requests here

    # ---- SHUTDOWN ----
    # Close MongoDB gracefully — flushes pending writes
    await close_mongo_connection()


# =============================================================================
# Application factory
# =============================================================================
app = FastAPI(
    title="TradeFlow AI",
    description=(
        "AI-powered trading signal platform for Indian & US equities, "
        "Crypto, Forex, and Commodities."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
    lifespan=lifespan,
    # Contact info shown in Swagger UI
    contact={
        "name": "TradeFlow AI",
        "url": "https://tradeflow.ai",
    },
)


# =============================================================================
# Health endpoints
# These are the MOST important routes — Nginx, Kubernetes, and monitoring
# all rely on these to know if the app is alive.
# =============================================================================

@app.get("/health", tags=["health"], summary="Basic health check")
async def health_check():
    """
    Returns 200 OK when the API process is running.
    Used by: Nginx upstream check, Kubernetes liveness probe.
    """
    return {
        "status": "ok",
        "service": "tradeflow-api",
        "version": "1.0.0",
        "env": settings.app_env,
    }


@app.get("/health/db", tags=["health"], summary="Database health check")
async def health_check_db():
    """
    Checks both PostgreSQL and MongoDB are reachable.
    Used by: Kubernetes readiness probe, Grafana dashboards.
    """
    status = {"postgres": "unknown", "mongodb": "unknown"}

    # ---- PostgreSQL ----
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception as exc:
        status["postgres"] = f"error: {exc}"

    # ---- MongoDB ----
    try:
        client = get_mongo_client()
        await client.admin.command("ping")
        status["mongodb"] = "ok"
    except Exception as exc:
        status["mongodb"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" for v in status.values()) else "degraded"

    return {"status": overall, "databases": status}


@app.get("/", tags=["health"], summary="Root — API info")
async def root():
    """API information and available endpoints."""
    return {
        "service": "TradeFlow AI",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "health_db": "/health/db",
        "routes": {
            "auth":      "/api/v1/auth",
            "data":      "/api/v1/data",
            "signals":   "/api/v1/signals",
            "backtest":  "/api/v1/backtest",
            "watchlist": "/api/v1/watchlist",
            "account":   "/api/v1/account",
        },
    }


# =============================================================================
# Register all routers
#
# Each router has:
#   prefix  → URL prefix for all routes in that router
#   tags    → Swagger UI grouping
#
# Example: auth router has GET /status
#          registered at → GET /api/v1/auth/status
# =============================================================================

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["auth"],
)
app.include_router(
    data.router,
    prefix="/api/v1/data",
    tags=["data"],
)
app.include_router(
    signals.router,
    prefix="/api/v1/signals",
    tags=["signals"],
)
app.include_router(
    backtest.router,
    prefix="/api/v1/backtest",
    tags=["backtest"],
)
app.include_router(
    watchlist.router,
    prefix="/api/v1/watchlist",
    tags=["watchlist"],
)
app.include_router(
    account.router,
    prefix="/api/v1/account",
    tags=["account"],
)
