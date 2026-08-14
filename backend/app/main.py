"""
TradeFlow AI — FastAPI Application
Day 9: Added config, database connections, and /health/db endpoint.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal, close_mongo_connection, get_mongo_client


# =============================================================================
# Lifespan — startup and shutdown logic
# Runs setup code BEFORE the app starts taking requests
# Runs cleanup code AFTER the app stops
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- STARTUP ----
    # Warm up the MongoDB connection so first request isn't slow
    get_mongo_client()

    yield  # app runs here, handling requests

    # ---- SHUTDOWN ----
    # Close MongoDB connection cleanly
    await close_mongo_connection()


# =============================================================================
# Create FastAPI app
# =============================================================================
app = FastAPI(
    title="TradeFlow AI",
    description="AI-powered trading signal platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# =============================================================================
# Routes
# =============================================================================

@app.get("/health")
async def health_check():
    """Basic health check — Nginx and Kubernetes hit this."""
    return {
        "status": "ok",
        "service": "tradeflow-api",
        "version": "1.0.0",
        "env": settings.app_env,
    }


@app.get("/health/db")
async def health_check_db():
    """
    Deep health check — verifies BOTH databases are reachable.
    Useful for debugging and monitoring dashboards.
    """
    status = {"postgres": "unknown", "mongodb": "unknown"}

    # --- Check PostgreSQL ---
    try:
        async with AsyncSessionLocal() as session:
            # SELECT 1 is the simplest possible query
            # If this works, the connection is alive
            await session.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"error: {str(e)}"

    # --- Check MongoDB ---
    try:
        client = get_mongo_client()
        # ping command returns {"ok": 1.0} if MongoDB is reachable
        await client.admin.command("ping")
        status["mongodb"] = "ok"
    except Exception as e:
        status["mongodb"] = f"error: {str(e)}"

    # Overall status — ok only if BOTH databases are ok
    overall = "ok" if all(v == "ok" for v in status.values()) else "degraded"

    return {
        "status": overall,
        "databases": status,
    }


@app.get("/")
async def root():
    return {
        "service": "TradeFlow AI",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "health_db": "/health/db",
    }
