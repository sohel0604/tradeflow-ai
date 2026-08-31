# Day 25 Notes — August 28, 2026
## Topic: Celery Pipeline Tasks — Everything Wires Together

---

## What we built today

The complete data pipeline as Celery tasks:

```
Celery Beat (06:00 IST)
      ↓
run_full_pipeline()           ← orchestrator task
      ↓ group() fan-out
fetch_yfinance_symbol(...)    ← one per symbol per timeframe (parallel)
fetch_binance_symbol(...)     ← one per crypto per timeframe (parallel)
      ↓ each task:
  YFinanceFetcher.fetch()
  DataCleaner.clean()
  upsert_price_bars()         → PostgreSQL price_bars
  log_fetch()                 → PostgreSQL fetch_logs
```

---

## group() — parallel fan-out

```python
tasks = [
    fetch_yfinance_symbol.s("RELIANCE.NS", "equity", "1d"),
    fetch_yfinance_symbol.s("RELIANCE.NS", "equity", "1h"),
    fetch_yfinance_symbol.s("TCS.NS",      "equity", "1d"),
    fetch_binance_symbol.s("BTCUSDT", "1d"),
    # ... 150+ more tasks
]

job = group(tasks)
result = job.apply_async()
```

`group()` = fan-out all tasks simultaneously.
With 4 Celery workers, 4 tasks run in parallel.
150 tasks / 4 workers = ~38 rounds of 4 = finishes 4x faster than serial.

`task.s()` = "signature" — creates a task blueprint without executing it.
This is how you pass tasks to group() without running them immediately.

---

## .run() vs .delay() vs .apply_async()

```python
# .run() — executes synchronously (bypasses Celery)
# Used in TESTS to call task logic directly
result = fetch_yfinance_symbol.run("RELIANCE.NS", "equity", "1d")

# .delay() — shorthand for .apply_async()
# Sends task to Redis queue, returns immediately
fetch_yfinance_symbol.delay("RELIANCE.NS", "equity", "1d")

# .apply_async() — full control over options
fetch_yfinance_symbol.apply_async(
    args=["RELIANCE.NS", "equity", "1d"],
    queue="pipeline",
    countdown=60,   # delay 60 seconds before running
)
```

In tests we use `.run()` because:
- Runs synchronously (no Redis needed)
- Returns the actual result (not an AsyncResult)
- We can assert on the return value immediately

In production the pipeline uses `.apply_async()` for real dispatch.

---

## Retry with exponential backoff

```python
@celery_app.task(
    bind=True,
    max_retries=3,
)
def fetch_yfinance_symbol(self, symbol, asset_type, timeframe):
    try:
        ...
    except Exception as exc:
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
            #          ↑    ↑
            #          60s  doubles each retry: 1, 2, 4
        )
```

Retry schedule for a failing task:
- Attempt 1:  fails → wait 60s  → retry
- Attempt 2:  fails → wait 120s → retry
- Attempt 3:  fails → wait 240s → retry
- Attempt 4:  fails → task marked FAILURE in Flower

Total wait before giving up: 7 minutes.
Long enough that transient network issues resolve.
Short enough that we get an alert quickly.

`self.request.retries` = current retry number (0 on first attempt).

---

## Isolation — one symbol's failure never stops others

```python
def fetch_yfinance_symbol(self, symbol, ...):
    try:
        df = _yfinance.fetch(...)
        if df.empty:
            log_fetch(symbol, timeframe, "FAILED", ...)
            return {"status": "FAILED"}   # ← returns, not raises

    except Exception:
        log_fetch(symbol, timeframe, "FAILED", ...)
        raise self.retry(...)             # ← retries this task only
```

If RELIANCE.NS fails:
- Its task logs FAILED and retries
- TCS.NS, BTCUSDT, EURUSD=X continue unaffected
- The pipeline completes with 149/150 symbols

Without this isolation:
- One failure → exception propagates to run_full_pipeline
- run_full_pipeline fails → all 150 symbols fail
- ops team sees 150 alerts instead of 1

---

## Module-level singletons in Celery tasks

```python
# Created ONCE when the module is imported
_yfinance = YFinanceFetcher()
_binance  = BinanceFetcher()
_cleaner  = DataCleaner()
```

Celery workers import the task module once at startup.
Module-level objects are created once and reused across all task calls.

If we created them inside the task function:
```python
def fetch_yfinance_symbol(self, ...):
    fetcher = YFinanceFetcher()  # created for every task call ← slow
```

That means 150 `YFinanceFetcher()` instantiations per pipeline run.
The requests.Session inside BinanceFetcher is especially expensive to create.
Singletons: created once, reused 150 times.

---

## Beat schedule — 06:00 IST = 00:30 UTC

```python
beat_schedule={
    "daily-pipeline-0630-IST": {
        "task":     "app.tasks.pipeline.run_full_pipeline",
        "schedule": crontab(hour=0, minute=30),
    }
}
```

IST = UTC + 5:30
06:00 IST = 00:30 UTC (midnight + 30 minutes)

`crontab(hour=0, minute=30)` fires at 00:30 UTC = 06:00 IST every day.

Why 06:00 IST?
- NSE opens at 09:15 IST
- 06:00 gives 3 hours to fetch + process + generate signals
- By 09:00 IST users have signals ready before market open

---

## How to trigger the pipeline manually

```bash
# From your terminal (while Docker is running)
docker compose exec celery_worker \
  celery -A app.celery_app call \
  app.tasks.pipeline.run_full_pipeline

# Fetch a single symbol manually
docker compose exec celery_worker \
  celery -A app.celery_app call \
  app.tasks.pipeline.fetch_binance_symbol \
  --args '["BTCUSDT", "1d"]'
```

---

## Tomorrow — Day 26
Technical indicator engine.
EMA, RSI, MACD, Bollinger Bands, ATR, OBV computed from price_bars
and stored in MongoDB indicators collection.
After tomorrow, the data pipeline is fully complete.
