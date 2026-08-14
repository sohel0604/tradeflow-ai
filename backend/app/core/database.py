"""
TradeFlow AI — Database Connections
Day 9: Sets up async PostgreSQL (SQLAlchemy) and async MongoDB (Motor).

Two databases, two different connection setups:
- PostgreSQL → SQLAlchemy (relational, structured data)
- MongoDB    → Motor (documents, flexible JSON data)

Both use async because FastAPI is async — blocking DB calls would
freeze the entire server while waiting for the database.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


# =============================================================================
# PostgreSQL — SQLAlchemy Async Setup
# =============================================================================

# The engine is the connection to PostgreSQL
# Think of it as the pipe between Python and PostgreSQL
# pool_size=10      → keep 10 connections open (reuse them, don't create new)
# max_overflow=20   → allow up to 20 extra if pool is full (burst traffic)
# pool_pre_ping=True → test connection before using it (handles stale connections)
# echo=False        → don't print every SQL query (set True to debug)
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.debug,  # prints SQL in development, silent in production
)

# Session factory — creates new database sessions
# A session = one "conversation" with the database
# expire_on_commit=False → don't expire objects after commit
#   (allows reading attributes after commit without extra queries)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    Base class for ALL SQLAlchemy models.

    Every model (PriceBar, User, Signal etc.) inherits from this.
    This is how SQLAlchemy knows which classes are database tables.

    Usage:
        from app.core.database import Base

        class PriceBar(Base):
            __tablename__ = "price_bars"
            id = Column(...)
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — provides a database session per request.

    Usage in a route:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    How it works:
    1. FastAPI calls get_db() before the route handler
    2. A session is created and yielded to the route
    3. After the route finishes, the session is closed
    4. If an error occurs, the session is rolled back first

    The 'yield' makes this a context manager — it runs setup BEFORE
    the route and cleanup AFTER (like a try/finally block).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # Something went wrong in the route handler
            # Roll back any partial changes to keep the DB consistent
            await session.rollback()
            raise
        finally:
            # Always close the session — return connection to pool
            await session.close()


# =============================================================================
# MongoDB — Motor Async Setup
# =============================================================================

# We use a module-level variable to hold the single client instance
# Motor (like SQLAlchemy) reuses connections — don't create a new client
# on every request
_mongo_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """
    Return the MongoDB client (create it if it doesn't exist).
    This is the 'singleton pattern' — one client shared by the whole app.
    """
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongo_uri)
    return _mongo_client


def get_mongo_db():
    """
    Return the MongoDB database object.
    Usage: db = get_mongo_db()  →  db["indicators"]
    """
    return get_mongo_client()[settings.mongo_db]


# ---------------------------------------------------------------------------
# Convenience functions — one per collection
# Import these wherever you need to touch MongoDB
# ---------------------------------------------------------------------------

def get_indicators_collection():
    """EMA, RSI, MACD, Bollinger per symbol per day."""
    return get_mongo_db()["indicators"]


def get_chart_patterns_collection():
    """Detected candlestick patterns per symbol."""
    return get_mongo_db()["chart_patterns"]


def get_backtest_trade_logs_collection():
    """Full trade-by-trade logs per backtest run."""
    return get_mongo_db()["backtest_trade_logs"]


def get_ai_conversations_collection():
    """Chat history with Claude AI assistant per user."""
    return get_mongo_db()["ai_conversations"]


def get_workflows_collection():
    """Automation workflow DAGs (prompt-to-workflow)."""
    return get_mongo_db()["workflows"]


def get_workflow_logs_collection():
    """Execution logs for each workflow run."""
    return get_mongo_db()["workflow_logs"]


async def close_mongo_connection():
    """
    Close MongoDB connection on app shutdown.
    Called in FastAPI lifespan — cleans up gracefully.
    """
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
