# Day 24 Notes — August 27, 2026
## Topic: PostgreSQL DB Writer — Bulk Upsert

---

## Why raw SQL instead of SQLAlchemy ORM for bulk inserts?

SQLAlchemy ORM insert (one row at a time):
```python
for row in df.iterrows():
    session.add(PriceBar(**row))  # 1 INSERT per row
session.commit()
# 1000 rows = 1000 round-trips to PostgreSQL ≈ 3 seconds
```

Raw SQL bulk insert:
```sql
INSERT INTO price_bars VALUES
  (uuid1, 'RELIANCE.NS', '1d', '2024-01-15', 2500, ...),
  (uuid2, 'RELIANCE.NS', '1d', '2024-01-16', 2510, ...),
  ...                                                       -- 1000 rows
ON CONFLICT DO NOTHING;
-- 1 round-trip to PostgreSQL ≈ 50ms
```

60x faster for 1000 rows. For a daily pipeline processing
50 symbols × 3 timeframes × 200+ rows each = 30,000 inserts.
That's 90 seconds (ORM) vs 1.5 seconds (raw SQL). Not negotiable.

---

## ON CONFLICT DO NOTHING — idempotency

```sql
INSERT INTO price_bars (symbol, timeframe, timestamp, ...)
VALUES (...)
ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING;
```

Three possible outcomes for each row:
1. Row doesn't exist → INSERT succeeds → counted in rowcount
2. Row already exists → silently skipped → NOT counted in rowcount
3. Any other error → raises exception

This means:
```python
rows_saved = upsert_price_bars(df)  # = rows actually inserted
```

If `rows_saved == 0`, all rows were already in the DB.
Not an error — just means the pipeline ran twice today.

---

## Sync vs async engines — the two-engine pattern

```
app/core/database.py      → AsyncEngine + asyncpg
  Used by: FastAPI routes (async def handlers)

app/services/data/db_writer.py → SyncEngine + psycopg2
  Used by: Celery tasks (synchronous worker threads)
```

Why can't Celery use the async engine?
```python
# Celery worker thread has no event loop
await session.execute(...)
# RuntimeError: no running event loop
```

Celery tasks run in regular Python threads.
Regular Python threads have no asyncio event loop.
AsyncIO operations require an event loop.
→ Celery must use the sync engine.

Same database. Two different connection pools.
One for async (FastAPI), one for sync (Celery).

---

## Singleton pattern for the engine

```python
_sync_engine = None

def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(...)  # created once
    return _sync_engine
```

Why singleton?
- Creating an engine is expensive (sets up connection pool)
- Creating a new engine on every Celery task = pool thrash
- Singleton: engine created once, connection pool reused forever

---

## _dataframe_to_records() — the important conversions

```python
# 1. pandas Timestamp → Python datetime
if hasattr(ts, "to_pydatetime"):
    ts = ts.to_pydatetime()
```
psycopg2 doesn't accept pandas Timestamps.
Must be Python datetime objects.

```python
# 2. numpy.float64 → Python float
"open": float(row["open"])
```
psycopg2 doesn't accept numpy types either.
`float(numpy.float64)` gives a plain Python float.

```python
# 3. timezone-naive → UTC
if ts.tzinfo is None:
    ts = ts.replace(tzinfo=timezone.utc)
```
PostgreSQL TIMESTAMPTZ requires timezone info.
Without it: "can't adapt type 'NoneType'" error.

---

## Integration tests vs unit tests

Unit tests (test_db_writer.py):
- Don't need PostgreSQL
- Test _dataframe_to_records() logic in isolation
- Run in milliseconds
- Run offline

Integration tests (test_db_writer_integration.py):
- Need real PostgreSQL running
- Test the full INSERT → SELECT round-trip
- Prove ON CONFLICT actually works
- Use a fake symbol "TESTSTOCK" — cleaned up after each test

```python
@pytest.fixture(autouse=True)
def cleanup_test_data():
    _delete_test_data()    # clean before
    yield
    _delete_test_data()    # clean after (even if test fails)
```

`autouse=True` means this fixture runs for EVERY test automatically.
You never need to call it manually.
Test data is always cleaned up — database stays pristine.

---

## The incremental fetch pattern

```python
# Day 1: full historical fetch
latest = get_latest_timestamp("RELIANCE.NS", "1d")
# → None (first time)
df = fetcher.fetch("RELIANCE.NS", "1d")  # 5 years of data
upsert_price_bars(df)

# Day 2: incremental fetch
latest = get_latest_timestamp("RELIANCE.NS", "1d")
# → 2024-01-15 (last bar we have)
next_start = latest + timedelta(days=1)
df = fetcher.fetch("RELIANCE.NS", "1d", start="2024-01-16")  # just yesterday
upsert_price_bars(df)
```

Instead of re-fetching 5 years every day (slow, hits rate limits),
we only fetch what's new. `get_latest_timestamp()` tells us where to start.

---

## Tomorrow — Day 25
Celery tasks: wire everything together.
`fetch_yfinance_symbol` and `fetch_binance_symbol` Celery tasks
that call: fetch → clean → upsert → log_fetch.
The first time real market data flows through the full pipeline.
