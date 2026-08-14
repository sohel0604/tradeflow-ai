"""
TradeFlow AI — FastAPI Application
Day 7: Minimal skeleton — just enough to prove the container starts.
We build out routes, middleware, and database connections from Day 15 onwards.
"""
from fastapi import FastAPI

# ---------------------------------------------------------------------------
# Create the FastAPI application instance
# title, description, version appear in the /docs Swagger UI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TradeFlow AI",
    description="AI-powered trading signal platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Health check — the most important endpoint
# Nginx, Kubernetes, and monitoring tools all hit this to know we're alive
# Must return 200 OK with {"status": "ok"}
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "tradeflow-api", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Root — basic info
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "service": "TradeFlow AI",
        "status":  "running",
        "docs":    "/docs",
        "health":  "/health",
    }
