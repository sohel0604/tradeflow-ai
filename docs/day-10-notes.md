# Day 10 Notes — August 13, 2026
## Topic: SQLAlchemy Models — PriceBar & FetchLog

---

## What is a SQLAlchemy Model?

A model is a Python class that maps to a database table.

```python
class PriceBar(Base):           # Python class
    __tablename__ = "price_bars" # → maps to this table in PostgreSQL

    id        = Column(UUID)     # → id column
    symbol    = Column(String)   # → symbol column
    close     = Column(Float)    # → close column
```

When you write:
```python
bar = PriceBar(symbol="RELIANCE.NS", close=2578.90)
session.add(bar)
await session.commit()
```

SQLAlchemy translates this to:
```sql
INSERT INTO price_bars (id, symbol, close, ...)
VALUES ('uuid-here', 'RELIANCE.NS', 2578.90, ...);
```

You write Python. SQLAlchemy writes SQL.

---

## PriceBar — breaking down the model

### UUID Primary Key
```python
id = Column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
)
```

`UUID(as_uuid=True)` → PostgreSQL `uuid` type, Python `uuid.UUID` object
`primary_key=True`   → this column uniquely identifies each row
`default=uuid.uuid4` → auto-generate a UUID when inserting (no manual ID needed)

Why `uuid.uuid4` (without brackets)?
- `uuid.uuid4` = the function itself (called each time a row is created)
- `uuid.uuid4()` = one UUID generated at import time (ALL rows get the same ID!)
This is a common Python mistake — always pass the function, not the result.

### DateTime with timezone
```python
timestamp = Column(DateTime(timezone=True), nullable=False)
```

`DateTime(timezone=True)` = PostgreSQL `TIMESTAMPTZ`
- Stores timezone offset with the datetime
- Always converted to UTC when stored
- Never use `DateTime()` without timezone — causes bugs in production

### Float columns
```python
open  = Column(Float, nullable=False)
high  = Column(Float, nullable=False)
low   = Column(Float, nullable=False)
close = Column(Float, nullable=False)
volume = Column(Float, nullable=False, default=0.0)
```

`nullable=False` → this column MUST have a value (NOT NULL in SQL)
`default=0.0` → Python-side default (used when not provided)

Note: `server_default` is a DB-side default (set in SQL).
`default` is a Python-side default (set before INSERT).
We use Python-side defaults for flexibility.

---

## __table_args__ — constraints and indexes

```python
__table_args__ = (
    UniqueConstraint(
        "symbol", "timeframe", "timestamp",
        name="uq_price_bars_symbol_tf_ts"
    ),
    Index("ix_price_bars_symbol_timeframe", "symbol", "timeframe"),
    Index("ix_price_bars_timestamp", "timestamp"),
    Index("ix_price_bars_asset_type", "asset_type"),
)
```

`__table_args__` is a tuple of table-level settings.
It's where you put things that involve multiple columns.

### UniqueConstraint
```python
UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_...")
```
This creates a UNIQUE constraint on the COMBINATION of 3 columns.
- (`RELIANCE.NS`, `1d`, `2024-01-15`) → allowed once ✅
- (`RELIANCE.NS`, `1d`, `2024-01-15`) → rejected on second insert ❌
- (`TCS.NS`, `1d`, `2024-01-15`) → allowed (different symbol) ✅

The `name=` parameter is important — Alembic uses it to identify
the constraint during migrations (drop/recreate if it changes).

### Index
```python
Index("ix_price_bars_symbol_timeframe", "symbol", "timeframe")
```
Creates a B-tree index on these two columns together.
Name convention: `ix_tablename_columns`

Without this index:
```sql
SELECT * FROM price_bars WHERE symbol='RELIANCE.NS' AND timeframe='1d'
-- PostgreSQL scans ALL rows → slow on 10M rows
```

With this index:
```sql
-- PostgreSQL jumps directly to RELIANCE.NS + 1d rows → fast
```

---

## FetchLog — why it matters

```python
class FetchLog(Base):
    symbol    = Column(String)  # which instrument
    status    = Column(String)  # "SUCCESS" or "FAILED"
    rows_saved = Column(Integer) # how many bars were inserted
    error_msg = Column(Text)    # what went wrong (if failed)
    fetched_at = Column(DateTime) # when
    source    = Column(String)  # "yfinance", "binance" etc.
```

Every single fetch attempt creates a FetchLog row.
This is called an audit log — you never delete it.

How it's used later:
```sql
-- Find symbols that failed for 2+ consecutive days (Day 36 ops alert)
SELECT symbol, COUNT(*) as failure_days
FROM fetch_logs
WHERE status = 'FAILED'
  AND fetched_at > NOW() - INTERVAL '3 days'
GROUP BY symbol, DATE(fetched_at)
HAVING COUNT(*) >= 2;
```

---

## models/__init__.py — why it exists

```python
from app.models.price import PriceBar, FetchLog
```

Alembic needs to import ALL models to know what tables to create.
By importing them in `__init__.py`, a single import of `app.models`
makes all models visible.

In `alembic/env.py` (Day 13) we'll write:
```python
import app.models  # imports __init__.py → imports all models
target_metadata = Base.metadata  # Alembic reads all table definitions
```

---

## What SQLAlchemy generates from our model

Our Python class creates this SQL (you can verify with Alembic):
```sql
CREATE TABLE price_bars (
    id         UUID NOT NULL,
    symbol     VARCHAR(50) NOT NULL,
    timeframe  VARCHAR(10) NOT NULL,
    timestamp  TIMESTAMPTZ NOT NULL,
    open       FLOAT NOT NULL,
    high       FLOAT NOT NULL,
    low        FLOAT NOT NULL,
    close      FLOAT NOT NULL,
    volume     FLOAT NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ,
    PRIMARY KEY (id),
    CONSTRAINT uq_price_bars_symbol_tf_ts UNIQUE (symbol, timeframe, timestamp)
);

CREATE INDEX ix_price_bars_symbol_timeframe ON price_bars (symbol, timeframe);
CREATE INDEX ix_price_bars_timestamp ON price_bars (timestamp);
CREATE INDEX ix_price_bars_asset_type ON price_bars (asset_type);
```

We write 80 lines of Python → SQLAlchemy generates 20 lines of SQL.

---

## Tomorrow — Day 11
Write the User, AuthToken, ApiKey and BrokerCredential models.
These are the auth foundation — every user action in the app
connects back to the User model.
