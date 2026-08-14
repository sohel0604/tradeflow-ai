# Day 8 Notes — August 11, 2026
## Topic: SQL Fundamentals

---

## Why learn SQL if we use SQLAlchemy (ORM)?

SQLAlchemy generates SQL for us automatically.
But you MUST understand SQL because:

1. When something goes wrong, you need to debug the raw query
2. Complex queries (aggregations, window functions) are easier in raw SQL
3. Alembic migrations are written in SQL
4. Understanding SQL makes you understand WHY the ORM does what it does
5. Every professional backend developer knows SQL

Think of SQLAlchemy as a car.
SQL is knowing how the engine works.
You can drive without knowing the engine — but when it breaks, you're stuck.

---

## The 5 most important SQL commands

```sql
SELECT  → read data
INSERT  → add data
UPDATE  → change data
DELETE  → remove data
CREATE  → make a new table
```

90% of your time is SELECT. Master that first.

---

## SELECT — the most important command

```sql
-- Basic: get everything
SELECT * FROM price_bars;

-- Better: get only what you need (faster, clearer)
SELECT symbol, timestamp, close FROM price_bars;

-- Filter rows
SELECT * FROM price_bars WHERE symbol = 'RELIANCE.NS';

-- Multiple conditions
SELECT * FROM price_bars
WHERE symbol = 'RELIANCE.NS'
  AND timeframe = '1d'
  AND timestamp >= '2024-01-01';

-- Sort results
SELECT * FROM price_bars ORDER BY timestamp DESC;

-- Limit results
SELECT * FROM price_bars ORDER BY timestamp DESC LIMIT 60;
```

**Rule:** Always use LIMIT in development.
Never run `SELECT * FROM price_bars` on a table with 10 million rows.

---

## Data types we use

| SQL Type | Python equivalent | Example |
|----------|------------------|---------|
| `VARCHAR(50)` | `str` | `"RELIANCE.NS"` |
| `FLOAT` | `float` | `2567.50` |
| `INTEGER` | `int` | `1000000` |
| `BOOLEAN` | `bool` | `True` / `False` |
| `TIMESTAMPTZ` | `datetime` (with tz) | `2024-01-15 00:00:00+00` |
| `UUID` | `uuid.UUID` | `a1b2c3d4-...` |
| `JSON` / `JSONB` | `dict` / `list` | `{"ema_9": 182.3}` |

**Always use TIMESTAMPTZ (not TIMESTAMP)**
TIMESTAMPTZ stores timezone information — so 06:00 IST is saved as 00:30 UTC.
TIMESTAMP without timezone causes bugs when servers are in different timezones.

---

## PRIMARY KEY vs UNIQUE constraint

```sql
-- PRIMARY KEY: one per table, uniquely identifies each row
id SERIAL PRIMARY KEY    -- auto-increments: 1, 2, 3, 4...

-- In our real app we use UUID instead of SERIAL:
id UUID PRIMARY KEY      -- e.g. a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

Why UUID over SERIAL?
- SERIAL: predictable (1, 2, 3) → attacker can guess IDs
- UUID: random → impossible to guess
- UUID works across multiple databases/services (no collision)

```sql
-- UNIQUE constraint: a combination of columns must be unique
UNIQUE (symbol, timeframe, timestamp)
```
This means: you can have many rows with symbol='RELIANCE.NS',
and many rows with timeframe='1d',
but you CANNOT have two rows with the SAME symbol+timeframe+timestamp.

This is how we prevent duplicate price bars.

---

## ON CONFLICT DO NOTHING — idempotency

This is one of the most important patterns in our pipeline:

```sql
INSERT INTO price_bars (symbol, timeframe, timestamp, close, ...)
VALUES ('RELIANCE.NS', '1d', '2024-01-15', 2578.90, ...)
ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING;
```

**Idempotent** = running the same operation multiple times
has the same effect as running it once.

Our daily pipeline fetches and inserts data every morning.
If it runs twice (due to a bug or retry), the second run
silently ignores duplicate rows instead of failing.

Without this: pipeline crashes, data corrupted.
With this: pipeline is bulletproof.

---

## INDEX — why they matter

Imagine looking up "RELIANCE.NS" in a 10-million row table.

Without index:
```
PostgreSQL reads every single row → checks if symbol = 'RELIANCE.NS'
→ 10,000,000 comparisons → SLOW (seconds)
```

With index on (symbol, timeframe):
```
PostgreSQL uses the index like a book index
→ jumps directly to RELIANCE.NS rows
→ ~100 comparisons → FAST (milliseconds)
```

We create indexes on columns we filter by most often:
```sql
CREATE INDEX ON price_bars (symbol, timeframe);   -- most queries filter by these
CREATE INDEX ON price_bars (timestamp);            -- date range queries
CREATE INDEX ON signals (symbol, signal_date);     -- signal lookups
```

Rule: Add an index whenever you have a WHERE clause on that column
and the table will have more than ~10,000 rows.

---

## GROUP BY + Aggregates — analytics queries

```sql
-- How many price bars do we have per symbol?
SELECT symbol, COUNT(*) AS bar_count
FROM price_bars
GROUP BY symbol
ORDER BY bar_count DESC;

-- What's the average closing price per symbol?
SELECT symbol, AVG(close) AS avg_close
FROM price_bars
GROUP BY symbol;
```

GROUP BY collapses all rows with the same value into one row.
Then you apply an aggregate function (COUNT, AVG, SUM, MAX, MIN) to each group.

We'll use this heavily for:
- Counting signals per strategy
- Computing average win rates
- Summarising fetch logs

---

## DISTINCT ON — get latest row per group

```sql
-- Get the most recent bar for each symbol
SELECT DISTINCT ON (symbol)
    symbol, timestamp, close
FROM price_bars
ORDER BY symbol, timestamp DESC;
```

This is a PostgreSQL-specific feature.
It picks ONE row per unique symbol value — the first one after sorting.
Since we sort by timestamp DESC, it picks the LATEST bar for each symbol.

We'll use this to get the current price of all instruments.

---

## The queries we'll use most in TradeFlow

```sql
-- Get last 60 bars for chart display (Day 22+)
SELECT timestamp, open, high, low, close, volume
FROM price_bars
WHERE symbol = 'RELIANCE.NS' AND timeframe = '1d'
ORDER BY timestamp DESC LIMIT 60;

-- Get latest indicators for a symbol (Day 39+)
SELECT * FROM indicators
WHERE symbol = 'RELIANCE.NS' AND timeframe = '1d'
ORDER BY timestamp DESC LIMIT 1;

-- Get all passing backtest results (Day 53+)
SELECT symbol, strategy, win_rate, avg_rr
FROM backtest_results
WHERE passed = TRUE
ORDER BY win_rate DESC;

-- Count open signals (Day 65+)
SELECT direction, COUNT(*) as count
FROM signals
WHERE outcome = 'OPEN'
GROUP BY direction;
```

---

## Run the practice queries yourself

```bash
# Start PostgreSQL
cd "/Users/sohelsmac/TradeFlow AI"
docker compose up -d postgres

# Wait 10 seconds for healthy status, then connect
docker compose exec postgres psql -U tradeflow -d tradeflow

# Inside psql, useful commands:
\dt              # list all tables
\d table_name    # describe a table (columns, types, constraints)
\l               # list databases
\q               # quit
```

Then copy-paste queries from `docs/sql-practice.sql` one by one.

---

## Tomorrow — Day 9
SQLAlchemy ORM setup.
We write Python classes (models) that map to database tables.
SQLAlchemy translates our Python into SQL automatically.
