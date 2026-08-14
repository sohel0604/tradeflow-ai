# Day 9 Notes — August 12, 2026
## Topic: SQLAlchemy ORM Setup

---

## What is an ORM?

ORM = Object Relational Mapper.

Without ORM — raw SQL in Python:
```python
cursor.execute("""
    SELECT id, symbol, close FROM price_bars
    WHERE symbol = %s ORDER BY timestamp DESC LIMIT 1
""", ("RELIANCE.NS",))
row = cursor.fetchone()
print(row[2])  # what is index 2? No idea without checking the query
```

With ORM — Python objects:
```python
bar = await session.scalar(
    select(PriceBar)
    .where(PriceBar.symbol == "RELIANCE.NS")
    .order_by(PriceBar.timestamp.desc())
    .limit(1)
)
print(bar.close)  # clear, readable, IDE gives autocomplete
```

The ORM translates Python objects and methods INTO SQL automatically.
You write Python, SQLAlchemy writes SQL.

---

## What we built today

### 3 files in `backend/app/core/`

```
backend/app/core/
├── __init__.py      ← makes it a Python package
├── config.py        ← reads .env, typed settings
└── database.py      ← async DB connections
```

---

## config.py — pydantic-settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_host: str = "postgres"
    postgres_password: str = "tradeflow123"
    debug: bool = True
```

pydantic-settings automatically:
- Reads `.env` file
- Maps `POSTGRES_HOST=postgres` to `settings.postgres_host`
- Converts `DEBUG=true` (string) to `True` (bool)
- Raises an error if a required variable is missing

```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()  # module-level — import this everywhere
```

`@lru_cache` = the function result is cached after the first call.
`.env` is read ONCE when the app starts — not on every request.

---

## database.py — SQLAlchemy async engine

### The engine
```python
engine = create_async_engine(
    settings.database_url,   # postgresql+asyncpg://user:pass@host/db
    pool_size=10,             # keep 10 connections open
    max_overflow=20,          # allow 20 extra in bursts
    pool_pre_ping=True,       # test connections before using
    echo=settings.debug,      # log all SQL in development
)
```

The engine = the connection pool.
It keeps N connections to PostgreSQL open and reuses them.
Creating a new DB connection takes ~50ms — pool avoids this overhead.

### The session
```python
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

A session = one unit of work with the database.
- Start session → run queries → commit → close
- Like a shopping cart: you add items (queries), then checkout (commit)

`expire_on_commit=False` — after committing, you can still read
the object's attributes without triggering another database query.

### The Base class
```python
class Base(DeclarativeBase):
    pass
```

This is the parent class for ALL our models.
When we write:
```python
class PriceBar(Base):
    __tablename__ = "price_bars"
```
SQLAlchemy knows PriceBar maps to the `price_bars` table.

### get_db() — the FastAPI dependency
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

This is a FastAPI "dependency" — it provides a session to every route.

```
Request comes in
    ↓
FastAPI calls get_db()
    ↓
Session is created
    ↓
Session is YIELDED to your route handler
    ↓
Route runs (uses session to query DB)
    ↓
Response sent to user
    ↓
Session is closed (returned to pool)
```

The `yield` is key — it lets get_db() run code both BEFORE
and AFTER the route handler, like a try/finally block.

---

## Async vs Sync — why it matters

### Sync (bad for APIs)
```python
# This BLOCKS the entire server while waiting for PostgreSQL
result = db.execute("SELECT * FROM price_bars")
# Server can't handle other requests during this wait
```

### Async (good for APIs)
```python
# This SUSPENDS this request and lets others run while waiting
result = await session.execute(select(PriceBar))
# Other requests are handled while we wait for PostgreSQL
```

With async, one FastAPI process can handle hundreds of
concurrent requests even while waiting for slow database queries.
Without async, each database query blocks ALL other users.

---

## MongoDB — Motor async client

```python
_mongo_client: AsyncIOMotorClient | None = None

def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongo_uri)
    return _mongo_client
```

This is the Singleton pattern — only one MongoDB client ever exists.
Motor manages a connection pool internally just like SQLAlchemy.

Usage in a route:
```python
collection = get_indicators_collection()
doc = await collection.find_one({"symbol": "BTCUSDT"})
```

---

## The /health/db endpoint

```python
@app.get("/health/db")
async def health_check_db():
    # Test PostgreSQL
    await session.execute(text("SELECT 1"))

    # Test MongoDB
    await client.admin.command("ping")

    return {"status": "ok", "databases": {"postgres": "ok", "mongodb": "ok"}}
```

`SELECT 1` — simplest possible query, returns immediately.
If this works, the database connection is alive.

`db.admin.command("ping")` — MongoDB equivalent of SELECT 1.
Returns `{"ok": 1.0}` if MongoDB is reachable.

This endpoint is hit by:
- Kubernetes liveness probes (is the app alive?)
- Grafana dashboards (is the DB connected?)
- Your own debugging (is the DB down?)

---

## Tomorrow — Day 10
Write the first real SQLAlchemy models:
`PriceBar` and `FetchLog` — the two tables we need
before we can start the data pipeline.
These are the Python classes that map to our SQL tables.
