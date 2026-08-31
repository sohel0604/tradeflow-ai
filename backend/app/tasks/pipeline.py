"""
TradeFlow AI — Data Pipeline Celery Tasks
Day 25: Fetch → Clean → Upsert → Log

Task hierarchy:
  run_full_pipeline()
      ↓ group() — all symbols in parallel
  fetch_yfinance_symbol(symbol, asset_type, timeframe)
  fetch_binance_symbol(symbol, timeframe)
      ↓ each task internally calls:
  YFinanceFetcher.fetch() or BinanceFetcher.fetch()
      ↓
  DataCleaner.clean()
      ↓
  upsert_price_bars(df)   → PostgreSQL
  log_fetch(...)          → fetch_logs table

Why Celery tasks instead of just running Python functions?
- Tasks run in separate worker processes (parallelism)
- Tasks retry automatically on failure (reliability)
- Tasks are visible in Flower dashboard (observability)
- Tasks can be scheduled (Celery Beat at 06:00 IST)
- Failed tasks don't crash the pipeline (isolation)
"""
from celery import group
from celery.schedules import crontab

import structlog

from app.celery_app import celery_app
from app.services.data.yfinance_fetcher import (
    YFinanceFetcher,
    ALL_YFINANCE_SYMBOLS,
)
from app.services.data.binance_fetcher import (
    BinanceFetcher,
    CRYPTO_SYMBOLS,
)
from app.services.data.cleaner import DataCleaner
from app.services.data.db_writer import upsert_price_bars, log_fetch

logger = structlog.get_logger(__name__)

# Module-level singletons — created once, reused across tasks
# This saves the overhead of instantiating them for every task call
_yfinance = YFinanceFetcher()
_binance  = BinanceFetcher()
_cleaner  = DataCleaner()

# Timeframes to fetch for each symbol
TIMEFRAMES = ["1d", "1h", "15m"]


# =============================================================================
# Pipeline orchestrator — run_full_pipeline
# =============================================================================

@celery_app.task(
    name="app.tasks.pipeline.run_full_pipeline",
    bind=True,
    max_retries=1,
)
def run_full_pipeline(self):
    """
    Entry point for the daily data pipeline.
    Triggered by Celery Beat at 06:00 IST (00:30 UTC).

    Creates a Celery group — one task per symbol per timeframe.
    All tasks run in parallel across available worker processes.

    group() = fan-out pattern:
      1 orchestrator task → N worker tasks (all run simultaneously)

    Example fan-out for 3 symbols × 3 timeframes = 9 tasks:
      fetch_yfinance_symbol("RELIANCE.NS", "equity", "1d")
      fetch_yfinance_symbol("RELIANCE.NS", "equity", "1h")
      fetch_yfinance_symbol("RELIANCE.NS", "equity", "15m")
      fetch_yfinance_symbol("TCS.NS",      "equity", "1d")
      ... etc
    """
    logger.info("pipeline_started")

    # Build yfinance task group
    yf_tasks = [
        fetch_yfinance_symbol.s(symbol, asset_type, tf)
        for symbol, asset_type in ALL_YFINANCE_SYMBOLS
        for tf in TIMEFRAMES
    ]

    # Build Binance task group
    binance_tasks = [
        fetch_binance_symbol.s(symbol, tf)
        for symbol in CRYPTO_SYMBOLS
        for tf in TIMEFRAMES
    ]

    all_tasks = yf_tasks + binance_tasks
    total     = len(all_tasks)

    # group() dispatches all tasks to the worker queue simultaneously
    # apply_async() sends the group without waiting for results
    job = group(all_tasks)
    result = job.apply_async()

    logger.info(
        "pipeline_dispatched",
        total_tasks=total,
        yf_tasks=len(yf_tasks),
        binance_tasks=len(binance_tasks),
        group_id=result.id,
    )

    return {
        "status":       "dispatched",
        "total_tasks":  total,
        "group_id":     result.id,
    }


# =============================================================================
# Per-symbol fetch tasks
# =============================================================================

@celery_app.task(
    name="app.tasks.pipeline.fetch_yfinance_symbol",
    bind=True,
    max_retries=3,
    default_retry_delay=60,      # 60 seconds between retries
)
def fetch_yfinance_symbol(self, symbol: str, asset_type: str, timeframe: str):
    """
    Fetch, clean, and store one yfinance symbol+timeframe.

    Retry logic:
    - max_retries=3: try up to 4 times total (1 original + 3 retries)
    - Exponential backoff: 60s, 120s, 240s between retries
    - If all retries fail: status=FAILED is logged, pipeline continues

    The task NEVER crashes the pipeline.
    If RELIANCE.NS fails, TCS.NS still gets processed.
    """
    logger.info("yfinance_task_start", symbol=symbol, timeframe=timeframe)

    try:
        # Step 1: Fetch raw data
        df = _yfinance.fetch(
            symbol=symbol,
            timeframe=timeframe,
            asset_type=asset_type,
        )

        if df.empty:
            log_fetch(symbol, timeframe, "FAILED", 0,
                      "Empty response from yfinance", "yfinance")
            logger.warning("yfinance_empty", symbol=symbol, timeframe=timeframe)
            return {"symbol": symbol, "timeframe": timeframe,
                    "status": "FAILED", "rows": 0}

        # Step 2: Clean
        df = _cleaner.clean(df, timeframe)

        if df.empty:
            log_fetch(symbol, timeframe, "FAILED", 0,
                      "All rows dropped by cleaner", "yfinance")
            return {"symbol": symbol, "timeframe": timeframe,
                    "status": "FAILED", "rows": 0}

        # Step 3: Store in PostgreSQL
        rows_saved = upsert_price_bars(df)

        # Step 4: Log success
        log_fetch(symbol, timeframe, "SUCCESS", rows_saved,
                  source="yfinance")

        logger.info(
            "yfinance_task_done",
            symbol=symbol,
            timeframe=timeframe,
            rows=rows_saved,
        )

        return {
            "symbol":    symbol,
            "timeframe": timeframe,
            "status":    "SUCCESS",
            "rows":      rows_saved,
        }

    except Exception as exc:
        error_msg = str(exc)
        log_fetch(symbol, timeframe, "FAILED", 0, error_msg, "yfinance")
        logger.error(
            "yfinance_task_error",
            symbol=symbol,
            timeframe=timeframe,
            error=error_msg,
        )
        # Retry with exponential backoff
        # countdown = 60 * 2^retries: 60s, 120s, 240s
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
        )


@celery_app.task(
    name="app.tasks.pipeline.fetch_binance_symbol",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def fetch_binance_symbol(self, symbol: str, timeframe: str):
    """
    Fetch, clean, and store one Binance crypto symbol+timeframe.
    Same pattern as fetch_yfinance_symbol.
    """
    logger.info("binance_task_start", symbol=symbol, timeframe=timeframe)

    try:
        # Step 1: Fetch
        df = _binance.fetch(
            symbol=symbol,
            timeframe=timeframe,
            asset_type="crypto",
        )

        if df.empty:
            log_fetch(symbol, timeframe, "FAILED", 0,
                      "Empty response from Binance", "binance")
            logger.warning("binance_empty", symbol=symbol, timeframe=timeframe)
            return {"symbol": symbol, "timeframe": timeframe,
                    "status": "FAILED", "rows": 0}

        # Step 2: Clean
        df = _cleaner.clean(df, timeframe)

        if df.empty:
            log_fetch(symbol, timeframe, "FAILED", 0,
                      "All rows dropped by cleaner", "binance")
            return {"symbol": symbol, "timeframe": timeframe,
                    "status": "FAILED", "rows": 0}

        # Step 3: Store
        rows_saved = upsert_price_bars(df)

        # Step 4: Log
        log_fetch(symbol, timeframe, "SUCCESS", rows_saved,
                  source="binance")

        logger.info(
            "binance_task_done",
            symbol=symbol,
            timeframe=timeframe,
            rows=rows_saved,
        )

        return {
            "symbol":    symbol,
            "timeframe": timeframe,
            "status":    "SUCCESS",
            "rows":      rows_saved,
        }

    except Exception as exc:
        error_msg = str(exc)
        log_fetch(symbol, timeframe, "FAILED", 0, error_msg, "binance")
        logger.error(
            "binance_task_error",
            symbol=symbol,
            timeframe=timeframe,
            error=error_msg,
        )
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
        )
