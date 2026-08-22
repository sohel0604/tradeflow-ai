"""
TradeFlow AI — FastAPI Application
Day 15: Route groups registered
Day 16: CORS + request logging middleware + exception handlers
Day 17: Structured logging configured + /config-check dev route
"""
import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.exceptions import (
    TradeFlowException,
    tradeflow_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.core.database import (
    AsyncSessionLocal,
    close_mongo_connection,
    get_mongo_client,
)
from app.api.v1.routes import (
    auth,
    data,
    signals,
    backtest,
    watchlist,
    account,
    config,
)

# ---------------------------------------------------------------------------
# Configure structured logging FIRST — before anything else logs
# ---------------------------------------------------------------------------
configure_logging()
logger = structlog.get_logger(__name__)


# =============================================================================
# Lifespan
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup",
        env=settings.app_env,
        debug=settings.debug,
        version="1.0.0",
    )

    # Warm up MongoDB connection pool
    get_mongo_client()

    # Create charts directory
    os.makedirs(settings.charts_dir, exist_ok=True)

    yield

    logger.info("shutdown")
    await close_mongo_connection()


# =============================================================================
# App factory
# =============================================================================
app = FastAPI(
    title="TradeFlow AI",
    description=(
        "AI-powered trading signal platform for Indian & US equities, "
        "Crypto, Forex, and Commodities."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# =============================================================================
# Middleware — ORDER MATTERS
# Middleware wraps the app like onion layers.
# The LAST middleware added is the FIRST to process each request.
#
# Request flow:
#   RequestLoggingMiddleware → CORSMiddleware → route handler
# Response flow:
#   route handler → CORSMiddleware → RequestLoggingMiddleware
# =============================================================================

# 1. CORS — must be early so preflight OPTIONS requests are handled
#    before hitting auth or rate limiting middleware
app.add_middleware(
    CORSMiddleware,
    # In production this comes from settings (e.g. "https://app.tradeflow.ai")
    # In development allows localhost:3000 (React) and localhost:5173 (Vite)
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,       # allow cookies / Authorization header
    allow_methods=["*"],          # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],          # Authorization, Content-Type, X-API-Key etc.
)

# 2. Request logging + correlation IDs
#    Wraps every request: adds correlation ID, times the request, logs it
app.add_middleware(RequestLoggingMiddleware)


# =============================================================================
# Exception handlers
# Registered in order of specificity — most specific first
# =============================================================================

# Our custom exceptions (NotFoundError, PlanLimitError etc.)
app.add_exception_handler(TradeFlowException, tradeflow_exception_handler)

# FastAPI/Starlette HTTP exceptions (404, 403, 422 etc.)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# Pydantic validation errors (missing fields, wrong types)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Catch-all for any unhandled exception → clean 500 response, no stack trace
app.add_exception_handler(Exception, global_exception_handler)


# =============================================================================
# Health endpoints
# =============================================================================

@app.get("/health", tags=["health"], summary="Basic health check")
async def health_check():
    """Returns 200 OK when the API is running."""
    return {
        "status": "ok",
        "service": "tradeflow-api",
        "version": "1.0.0",
        "env": settings.app_env,
    }


@app.get("/health/db", tags=["health"], summary="Database health check")
async def health_check_db():
    """Checks PostgreSQL and MongoDB are reachable."""
    db_status = {"postgres": "unknown", "mongodb": "unknown"}

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status["postgres"] = "ok"
    except Exception as exc:
        db_status["postgres"] = f"error: {exc}"

    try:
        client = get_mongo_client()
        await client.admin.command("ping")
        db_status["mongodb"] = "ok"
    except Exception as exc:
        db_status["mongodb"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" for v in db_status.values()) else "degraded"
    return {"status": overall, "databases": db_status}


@app.get("/", tags=["health"], summary="API info")
async def root():
    return {
        "service": "TradeFlow AI",
        "version": "1.0.0",
        "docs": "/docs",
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
# Routers
# =============================================================================
app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["auth"])
app.include_router(data.router,      prefix="/api/v1/data",      tags=["data"])
app.include_router(signals.router,   prefix="/api/v1/signals",   tags=["signals"])
app.include_router(backtest.router,  prefix="/api/v1/backtest",  tags=["backtest"])
app.include_router(watchlist.router, prefix="/api/v1/watchlist", tags=["watchlist"])
app.include_router(account.router,   prefix="/api/v1/account",   tags=["account"])

# Dev-only config check route (blocked in production)
app.include_router(config.router, prefix="/api/v1/dev", tags=["dev"])
