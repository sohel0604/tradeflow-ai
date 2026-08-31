"""
TradeFlow AI — PostgreSQL DB Writer
Day 24: Bulk upsert cleaned OHLCV data into price_bars.

Why synchronous SQLAlchemy here (not async)?
- Celery workers run in their own threads, not an async event loop
- asyncpg requires a running event loop to work
- Using the sync engine in Celery avoids "no running event loop" errors
- FastAPI routes use the async engine (app/core/database.py)
- Celery tasks use the sync engine (this file)

Two engines, one database:
  FastAPI  → AsyncEngine  (asyncpg driver)
  Celery   → SyncEngine   (psycopg2 driver)

The bulk upsert strategy:
  INSERT INTO price_bars (...) VALUES (...), (...), (...)
  ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING

"DO NOTHING" makes this idempotent — safe to re-run any number of times.
Re-running the pipeline never creates duplicate rows.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Synchronous SQLAlchemy engine — used by Celery tasks
# Only created once (module-level singleton pattern)
# ---------------------------------------------------------------------------
_sync_engine = None
_SyncSession = None


def _get_sync_engine():
    """Return the synchronous engine, creating it on first call."""
    global _sync_engine, _SyncSession

    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.database_url_sync,
            pool_size=5,          # keep 5 connections open
            max_overflow=10,      # allow 10 extra under load
            pool_pre_ping=True,   # test connection before using
            echo=False,           # don't log every SQL (too noisy in Celery)
        )
        _SyncSession = sessionmaker(
            bind=_sync_engine,
            autocommit=False,
            autoflush=False,
        )
        logger.debug("sync_engine_created")

    return _sync_engine, _SyncSession


def get_sync_session() -> Session:
    """Return a new synchronous session. Caller is responsible for closing."""
    _, SyncSession = _get_sync_engine()
    return SyncSession()


# ---------------------------------------------------------------------------
# Main public functions
# ---------------------------------------------------------------------------

def upsert_price_bars(df: pd.DataFrame) -> int:
    """
    Bulk-insert cleaned OHLCV rows into price_bars.

    Uses raw SQL for maximum performance — SQLAlchemy ORM would generate
    one INSERT per row; raw SQL generates one INSERT with N value tuples.

    For 1000 rows:
      ORM:     ~3 seconds  (1000 round-trips to PostgreSQL)
      Raw SQL: ~0.05 seconds (1 round-trip, 1000 value tuples) ← we use this

    ON CONFLICT DO NOTHING:
    - If a row with the same (symbol, timeframe, timestamp) already exists,
      skip it silently
    - PostgreSQL returns rowcount = number of rows actually inserted
    - Rows skipped by conflict = NOT counted in rowcount

    Returns:
        Number of rows actually inserted (0 if all were duplicates)
    """
    if df.empty:
        return 0

    # Build list of dicts — one per row to insert
    records = _dataframe_to_records(df)
    if not records:
        return 0

    session = get_sync_session()
    try:
        result = session.execute(
            text("""
                INSERT INTO price_bars
                    (id, symbol, timeframe, timestamp,
                     open, high, low, close, volume, asset_type, created_at)
                VALUES
                    (:id, :symbol, :timeframe, :timestamp,
                     :open, :high, :low, :close, :volume, :asset_type, :created_at)
                ON CONFLICT (symbol, timeframe, timestamp)
                DO NOTHING
            """),
            records,
        )
        session.commit()

        rows_inserted = result.rowcount if result.rowcount >= 0 else len(records)
        logger.debug(
            "upsert_complete",
            rows_attempted=len(records),
            rows_inserted=rows_inserted,
        )
        return rows_inserted

    except Exception as exc:
        session.rollback()
        logger.error("upsert_failed", error=str(exc))
        raise  # re-raise so the Celery task can log FAILED status
    finally:
        session.close()


def log_fetch(
    symbol: str,
    timeframe: str,
    status: str,
    rows_saved: int = 0,
    error_msg: Optional[str] = None,
    source: str = "yfinance",
) -> None:
    """
    Insert one row into fetch_logs.

    Called after EVERY fetch attempt — success or failure.
    This is the audit trail used by:
    - Ops alert system (Day 29) to detect consecutive failures
    - Debugging: "why is RELIANCE.NS missing data for 3 days?"

    Never raises — if the log insert fails, we log the failure
    to structlog but don't crash the pipeline.
    """
    session = get_sync_session()
    try:
        session.execute(
            text("""
                INSERT INTO fetch_logs
                    (id, symbol, timeframe, status,
                     rows_saved, error_msg, fetched_at, source)
                VALUES
                    (:id, :symbol, :timeframe, :status,
                     :rows_saved, :error_msg, NOW(), :source)
            """),
            {
                "id":         uuid.uuid4(),
                "symbol":     symbol,
                "timeframe":  timeframe,
                "status":     status,
                "rows_saved": rows_saved,
                "error_msg":  error_msg,
                "source":     source,
            },
        )
        session.commit()
    except Exception as exc:
        session.rollback()
        # Don't raise — logging failure must never crash the pipeline
        logger.error("fetch_log_insert_failed", error=str(exc))
    finally:
        session.close()


def get_latest_timestamp(symbol: str, timeframe: str) -> Optional[datetime]:
    """
    Return the most recent timestamp we have for a symbol+timeframe.

    Used by the pipeline to do incremental fetches:
    instead of re-fetching 5 years of data daily,
    we only fetch from the latest stored bar to today.

    Returns None if no data exists yet (first fetch).
    """
    session = get_sync_session()
    try:
        row = session.execute(
            text("""
                SELECT MAX(timestamp) AS latest
                FROM price_bars
                WHERE symbol   = :symbol
                  AND timeframe = :timeframe
            """),
            {"symbol": symbol.upper(), "timeframe": timeframe},
        ).fetchone()

        return row.latest if row and row.latest else None
    finally:
        session.close()


def count_rows(symbol: str, timeframe: str) -> int:
    """
    Return total number of stored bars for a symbol+timeframe.
    Used for validation and health checks.
    """
    session = get_sync_session()
    try:
        row = session.execute(
            text("""
                SELECT COUNT(*) AS cnt
                FROM price_bars
                WHERE symbol    = :symbol
                  AND timeframe = :timeframe
            """),
            {"symbol": symbol.upper(), "timeframe": timeframe},
        ).fetchone()
        return row.cnt if row else 0
    finally:
        session.close()


def get_consecutive_failures(symbol: str, days: int = 2) -> int:
    """
    Return the number of consecutive FAILED days for a symbol.
    Used by the ops alert system (Day 29).

    'Consecutive' means: every one of the last N calendar days
    had at least one FAILED fetch and zero SUCCESS fetches.
    """
    session = get_sync_session()
    try:
        rows = session.execute(
            text("""
                WITH daily AS (
                    SELECT
                        DATE(fetched_at AT TIME ZONE 'UTC') AS fetch_date,
                        MAX(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) AS had_success
                    FROM fetch_logs
                    WHERE symbol = :symbol
                      AND fetched_at > NOW() - INTERVAL '7 days'
                    GROUP BY DATE(fetched_at AT TIME ZONE 'UTC')
                    ORDER BY fetch_date DESC
                    LIMIT :days
                )
                SELECT COUNT(*) AS consecutive_failures
                FROM daily
                WHERE had_success = 0
            """),
            {"symbol": symbol, "days": days},
        ).fetchone()

        return rows.consecutive_failures if rows else 0
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------

def _dataframe_to_records(df: pd.DataFrame) -> list[dict]:
    """
    Convert a cleaned DataFrame into a list of dicts for SQLAlchemy execute().

    Key operations:
    - Generate a UUID for each row (DB doesn't auto-generate for us)
    - Convert pandas Timestamp to Python datetime (SQLAlchemy requirement)
    - Ensure timezone is UTC
    - Cast all values to Python native types (not numpy types)
      because psycopg2 doesn't accept numpy.float64 directly
    """
    records = []
    now = datetime.now(timezone.utc)

    for _, row in df.iterrows():
        ts = row["timestamp"]

        # Convert pandas Timestamp to Python datetime
        if hasattr(ts, "to_pydatetime"):
            ts = ts.to_pydatetime()

        # Ensure UTC-aware
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        records.append({
            "id":         uuid.uuid4(),
            "symbol":     str(row["symbol"]).upper(),
            "timeframe":  str(row["timeframe"]),
            "timestamp":  ts,
            "open":       float(row["open"]),
            "high":       float(row["high"]),
            "low":        float(row["low"]),
            "close":      float(row["close"]),
            "volume":     float(row.get("volume", 0.0)),
            "asset_type": str(row.get("asset_type", "equity")),
            "created_at": now,
        })

    return records
