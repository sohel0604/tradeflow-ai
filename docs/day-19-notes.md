# Day 19 Notes — August 22, 2026
## Topic: Async MongoDB Queries from FastAPI

---

## Why a service layer?

We could query MongoDB directly in the route handler:
```python
@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str):
    collection = get_indicators_collection()  # raw MongoDB
    doc = await collection.find_one({"symbol": symbol})
    return doc
```

This works but has problems:
- Route handler is doing too much (HTTP + business logic + DB query)
- Can't reuse the query logic elsewhere (e.g. in Celery tasks)
- Hard to test (need real MongoDB running)
- If MongoDB changes, need to update every route file

With a service layer:
```python
# Service handles the query logic
class IndicatorService:
    async def get_latest(self, symbol: str) -> dict:
        return await self.collection.find_one({"symbol": symbol}, sort=[("timestamp", -1)])

# Route is thin — just HTTP
@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str):
    doc = await indicators.get_latest(symbol)  # clean, one line
    if not doc:
        raise HTTPException(404, ...)
    return doc
```

The service layer is the bridge between HTTP and the database.

---

## Motor — async MongoDB driver

Motor is the async version of PyMongo.
```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://user:pass@host/db")
collection = client["tradeflow"]["indicators"]
```

All Motor operations are `async`:
```python
doc  = await collection.find_one({"symbol": "BTCUSDT"})
docs = await collection.find({}).to_list(length=100)
await collection.update_one(filter, update, upsert=True)
await collection.create_index([("symbol", 1)])
```

Without `await`: returns a coroutine object (not the result).
With `await`: suspends until MongoDB responds, then returns the result.

---

## MongoDB query operators

```python
# Exact match
{"symbol": "RELIANCE.NS"}

# Greater than / less than
{"signal_value": {"$gt": 0}}    # signal_value > 0 (bullish)
{"signal_value": {"$lt": 0}}    # signal_value < 0 (bearish)

# Date range
{"timestamp": {"$gte": since}}  # timestamp >= 5 days ago

# Nested field (dot notation)
{"indicators.rsi_14": {"$gt": 70}}  # RSI overbought
```

---

## sort, limit, projection

```python
await collection.find_one(
    {"symbol": "BTCUSDT"},
    sort=[("timestamp", -1)],          # -1 = descending (newest first)
    projection={"_id": 0},             # exclude MongoDB's _id field
)
```

`sort=[("timestamp", -1)]` — newest document first.
`projection={"_id": 0}` — exclude `_id` from the response.
  MongoDB always adds `_id` unless you explicitly exclude it.
  We exclude it because our API clients don't need it.

For get_history:
```python
cursor = collection.find(query, sort=[...], limit=100)
docs = await cursor.to_list(length=100)
```

`.find()` returns a cursor (like a generator — lazy evaluation).
`.to_list(length=N)` materialises the cursor into a Python list.
Always specify `length=` to prevent unbounded memory usage.

---

## upsert=True — idempotent writes

```python
await collection.update_one(
    {"symbol": symbol, "timeframe": tf, "timestamp": ts},  # match
    {"$set": {"indicators": {...}}},                        # update
    upsert=True,  # insert if not found, update if found
)
```

Same as PostgreSQL's `ON CONFLICT DO NOTHING` but for MongoDB.
The pipeline can re-run daily — same document just gets updated,
never duplicated.

`$set` — only update the specified fields.
Without `$set`, the entire document would be replaced.

---

## MongoDB indexes — why they matter here too

```python
await collection.create_index(
    [("symbol", 1), ("timeframe", 1), ("timestamp", -1)],
    unique=True,
    name="ix_indicators_symbol_tf_ts",
)
```

Without index: MongoDB scans ALL documents to find `symbol=BTCUSDT`.
With index: MongoDB jumps directly to BTCUSDT documents.

`unique=True` — prevents duplicate indicator snapshots
(same as UniqueConstraint in PostgreSQL).

We create indexes at app startup in the lifespan function:
```python
async with lifespan(app):
    await indicators.ensure_indexes()
    await chart_patterns.ensure_indexes()
```

`create_index` is idempotent — safe to call every startup.
If the index exists, MongoDB does nothing.

---

## FastAPI Query() params

```python
@router.get("/indicators/{symbol}")
async def get_indicators(
    symbol: str,                                 # path param
    timeframe: str = Query(
        default="1d",
        regex="^(1d|1h|15m)$",                  # must match this pattern
        description="Bar timeframe",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,                                  # max 500 rows
    ),
):
```

`Query()` adds validation to query parameters (URL params after `?`).
- `regex=` validates the string format
- `ge=`, `le=` validate numeric ranges
- `description=` appears in Swagger UI at /docs
- `default=` makes the param optional

Without `Query()`:
```python
timeframe: str = "1d"  # accepts ANY string — "banana" is valid
```

With `Query(regex=...)`:
```python
timeframe: str = Query("1d", regex="^(1d|1h|15m)$")  # only valid values
```

---

## What routes are live now

```
GET /api/v1/data/indicators/{symbol}         ← latest snapshot
GET /api/v1/data/indicators/{symbol}/history ← N snapshots
GET /api/v1/data/patterns/{symbol}           ← recent patterns
```

These return empty/404 right now because the pipeline hasn't run yet.
Once we build the Celery fetcher (Day 33) and indicator engine (Day 41),
these endpoints will return real data automatically.

---

## Tomorrow — Day 20
Global exception handler review + `/health/db` extended
to also test the MongoDB index creation.
Then we start the data pipeline — yfinance fetcher (Day 22).
