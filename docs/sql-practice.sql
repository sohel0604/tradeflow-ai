-- =============================================================================
-- TradeFlow AI — SQL Practice Queries
-- Day 8 — August 11, 2026
--
-- HOW TO RUN THESE:
--   1. Start PostgreSQL: docker compose up -d postgres
--   2. Connect:          docker compose exec postgres psql -U tradeflow -d tradeflow
--   3. Copy-paste any query below and press Enter
--   4. Type \q to exit
-- =============================================================================


-- =============================================================================
-- SECTION 1: CREATE TABLE
-- Understanding table structure before we use SQLAlchemy to generate it
-- =============================================================================

-- Create a simple practice table
-- This is what our price_bars table will look like
CREATE TABLE IF NOT EXISTS practice_price_bars (
    id          SERIAL PRIMARY KEY,         -- auto-incrementing integer ID
    symbol      VARCHAR(50) NOT NULL,       -- e.g. "RELIANCE.NS"
    timeframe   VARCHAR(10) NOT NULL,       -- e.g. "1d", "1h", "15m"
    timestamp   TIMESTAMPTZ NOT NULL,       -- timezone-aware datetime
    open        FLOAT NOT NULL,             -- opening price
    high        FLOAT NOT NULL,             -- highest price
    low         FLOAT NOT NULL,             -- lowest price
    close       FLOAT NOT NULL,             -- closing price
    volume      FLOAT NOT NULL DEFAULT 0,   -- trading volume
    asset_type  VARCHAR(20) NOT NULL        -- "equity", "crypto", "forex"
);

-- What does each constraint mean?
-- PRIMARY KEY  → uniquely identifies each row, auto-increments
-- NOT NULL     → this column MUST have a value, never empty
-- DEFAULT 0    → if no volume provided, use 0
-- VARCHAR(50)  → text up to 50 characters
-- FLOAT        → decimal number (e.g. 2567.45)
-- TIMESTAMPTZ  → timestamp WITH timezone (always store in UTC)


-- =============================================================================
-- SECTION 2: INSERT
-- Adding data to a table
-- =============================================================================

-- Insert a single row
INSERT INTO practice_price_bars
    (symbol, timeframe, timestamp, open, high, low, close, volume, asset_type)
VALUES
    ('RELIANCE.NS', '1d', '2024-01-15 00:00:00+00', 2567.50, 2589.00, 2551.25, 2578.90, 4521000, 'equity');

-- Insert multiple rows at once (faster than one by one)
INSERT INTO practice_price_bars
    (symbol, timeframe, timestamp, open, high, low, close, volume, asset_type)
VALUES
    ('RELIANCE.NS', '1d', '2024-01-16 00:00:00+00', 2578.90, 2601.50, 2570.00, 2595.30, 3987000, 'equity'),
    ('RELIANCE.NS', '1d', '2024-01-17 00:00:00+00', 2595.30, 2612.75, 2588.00, 2605.60, 4112000, 'equity'),
    ('TCS.NS',      '1d', '2024-01-15 00:00:00+00', 3821.00, 3845.50, 3810.25, 3835.90, 2341000, 'equity'),
    ('TCS.NS',      '1d', '2024-01-16 00:00:00+00', 3835.90, 3862.00, 3828.75, 3851.20, 1987000, 'equity'),
    ('BTCUSDT',     '1d', '2024-01-15 00:00:00+00', 42150.00, 43200.00, 41800.00, 42900.50, 18750.5, 'crypto'),
    ('BTCUSDT',     '1d', '2024-01-16 00:00:00+00', 42900.50, 44100.00, 42500.00, 43850.75, 21340.8, 'crypto'),
    ('EURUSD=X',    '1d', '2024-01-15 00:00:00+00', 1.0921, 1.0945, 1.0908, 1.0932, 0, 'forex');


-- =============================================================================
-- SECTION 3: SELECT — Reading data
-- The most important SQL operation
-- =============================================================================

-- Get all rows (use carefully on large tables!)
SELECT * FROM practice_price_bars;

-- Get specific columns only
SELECT symbol, timestamp, close FROM practice_price_bars;

-- Filter with WHERE
SELECT * FROM practice_price_bars
WHERE symbol = 'RELIANCE.NS';

-- Multiple conditions with AND
SELECT * FROM practice_price_bars
WHERE symbol = 'RELIANCE.NS'
  AND timeframe = '1d';

-- Filter by asset type
SELECT * FROM practice_price_bars
WHERE asset_type = 'crypto';

-- Filter by date range
SELECT * FROM practice_price_bars
WHERE timestamp >= '2024-01-16 00:00:00+00';

-- Find all rows where close > open (green candle = price went up)
SELECT symbol, timestamp, open, close,
       close - open AS price_change
FROM practice_price_bars
WHERE close > open;


-- =============================================================================
-- SECTION 4: ORDER BY — Sorting results
-- =============================================================================

-- Sort by timestamp newest first
SELECT * FROM practice_price_bars
ORDER BY timestamp DESC;

-- Sort by symbol then by timestamp
SELECT * FROM practice_price_bars
ORDER BY symbol ASC, timestamp ASC;

-- Get the most recent bar for each symbol
SELECT DISTINCT ON (symbol)
    symbol, timestamp, close
FROM practice_price_bars
ORDER BY symbol, timestamp DESC;


-- =============================================================================
-- SECTION 5: LIMIT — Control how many rows you get back
-- =============================================================================

-- Get only the last 3 rows
SELECT * FROM practice_price_bars
ORDER BY timestamp DESC
LIMIT 3;

-- Pagination: skip first 2 rows, get next 3
-- This is how we'll build pagination in our API
SELECT * FROM practice_price_bars
ORDER BY timestamp DESC
LIMIT 3 OFFSET 2;


-- =============================================================================
-- SECTION 6: Aggregate Functions — COUNT, SUM, AVG, MAX, MIN
-- =============================================================================

-- How many rows total?
SELECT COUNT(*) AS total_rows FROM practice_price_bars;

-- How many rows per symbol?
SELECT symbol, COUNT(*) AS bar_count
FROM practice_price_bars
GROUP BY symbol;

-- Average closing price per symbol
SELECT symbol, ROUND(AVG(close)::NUMERIC, 2) AS avg_close
FROM practice_price_bars
GROUP BY symbol;

-- Highest price ever seen per symbol
SELECT symbol, MAX(high) AS all_time_high, MIN(low) AS all_time_low
FROM practice_price_bars
GROUP BY symbol;

-- Total volume per asset type
SELECT asset_type, SUM(volume) AS total_volume
FROM practice_price_bars
GROUP BY asset_type;


-- =============================================================================
-- SECTION 7: UNIQUE CONSTRAINT — Preventing duplicate data
-- This is critical for our price pipeline (idempotency)
-- =============================================================================

-- Add a unique constraint so we can't insert duplicate symbol+timeframe+timestamp
ALTER TABLE practice_price_bars
ADD CONSTRAINT uq_practice_symbol_tf_ts
UNIQUE (symbol, timeframe, timestamp);

-- Now try to insert a duplicate row — it will FAIL with an error
-- Uncomment to test:
-- INSERT INTO practice_price_bars
--     (symbol, timeframe, timestamp, open, high, low, close, volume, asset_type)
-- VALUES
--     ('RELIANCE.NS', '1d', '2024-01-15 00:00:00+00', 9999, 9999, 9999, 9999, 0, 'equity');
-- ERROR: duplicate key value violates unique constraint

-- INSERT with ON CONFLICT DO NOTHING — idempotent!
-- Run this 10 times, only the first insert actually saves data
INSERT INTO practice_price_bars
    (symbol, timeframe, timestamp, open, high, low, close, volume, asset_type)
VALUES
    ('RELIANCE.NS', '1d', '2024-01-15 00:00:00+00', 9999, 9999, 9999, 9999, 0, 'equity')
ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING;

-- Verify: the original row is unchanged
SELECT * FROM practice_price_bars
WHERE symbol = 'RELIANCE.NS' AND timestamp = '2024-01-15 00:00:00+00';


-- =============================================================================
-- SECTION 8: UPDATE — Changing existing data
-- =============================================================================

-- Fix a wrong volume value
UPDATE practice_price_bars
SET volume = 4521000
WHERE symbol = 'RELIANCE.NS'
  AND timestamp = '2024-01-15 00:00:00+00';

-- Always use WHERE with UPDATE — without it you update EVERY row!


-- =============================================================================
-- SECTION 9: DELETE — Removing data
-- =============================================================================

-- Delete a specific row
DELETE FROM practice_price_bars
WHERE symbol = 'EURUSD=X';

-- Always use WHERE with DELETE — without it you delete EVERY row!

-- Verify it's gone
SELECT COUNT(*) FROM practice_price_bars WHERE symbol = 'EURUSD=X';
-- Should return 0


-- =============================================================================
-- SECTION 10: INDEX — Making queries fast
-- =============================================================================

-- Without an index, PostgreSQL scans EVERY row to find matches (slow)
-- With an index, PostgreSQL jumps directly to matching rows (fast)

-- We'll query price_bars by symbol + timeframe millions of times
-- So we create an index on these columns
CREATE INDEX IF NOT EXISTS idx_practice_symbol_timeframe
ON practice_price_bars (symbol, timeframe);

-- Also index by timestamp for date range queries
CREATE INDEX IF NOT EXISTS idx_practice_timestamp
ON practice_price_bars (timestamp);

-- See all indexes on the table
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'practice_price_bars';


-- =============================================================================
-- SECTION 11: QUERIES WE'LL USE IN THE REAL APP
-- These exact patterns appear in our Python code later
-- =============================================================================

-- Get last N bars for a symbol (used by chart API — Day 22)
SELECT timestamp, open, high, low, close, volume
FROM practice_price_bars
WHERE symbol = 'RELIANCE.NS'
  AND timeframe = '1d'
ORDER BY timestamp DESC
LIMIT 60;

-- Check if data exists before fetching (idempotency check)
SELECT MAX(timestamp) AS last_bar_date
FROM practice_price_bars
WHERE symbol = 'RELIANCE.NS'
  AND timeframe = '1d';

-- Count rows per symbol to check data quality
SELECT
    symbol,
    timeframe,
    COUNT(*)           AS total_bars,
    MIN(timestamp)     AS first_bar,
    MAX(timestamp)     AS last_bar,
    MAX(timestamp) - MIN(timestamp) AS data_span
FROM practice_price_bars
GROUP BY symbol, timeframe
ORDER BY symbol, timeframe;


-- =============================================================================
-- CLEANUP — Remove practice table when done
-- =============================================================================

-- DROP TABLE practice_price_bars;
-- Uncomment when you're done practicing
