# Day 23 Notes — August 26, 2026
## Topic: Data Cleaning Module

---

## Why clean data before storing?

Raw data from APIs has real-world problems.
If you store dirty data your indicators and signals will be wrong.

Example: RSI-14 needs 14 consecutive bars.
If you have a gap (missing Tuesday), the 14-bar window is off by one.
Your RSI reads 65 instead of 70 — wrong signal, wrong trade.

The cleaner guarantees:
- No missing bars in the time series
- No duplicate rows
- All prices are valid floats > 0
- All timestamps are UTC

---

## The 6 cleaning steps

```
Raw DataFrame
      ↓
Step 1: Normalise timestamps → UTC timezone-aware
      ↓
Step 2: Enforce float64 on OHLCV
      ↓
Step 3: Remove duplicates on (symbol, timeframe, timestamp)
      ↓
Step 4: Sort by timestamp chronologically
      ↓
Step 5: Forward-fill missing business days (daily only)
      ↓
Step 6: Drop rows with zero, negative, or NaN prices
      ↓
Clean DataFrame → DB Writer
```

Each step is a separate method so it's easy to:
- Test individually
- Skip specific steps (e.g. skip gap-fill for intraday)
- Debug which step removed a row

---

## Step 5: Forward-fill gaps — the most important step

```python
full_range = pd.date_range(
    start=df.index.min(),
    end=df.index.max(),
    freq="B",          # "B" = business days, skips weekends automatically
    tz="UTC",
)

df = df.reindex(full_range)   # inserts NaN rows for missing dates

df["close"] = df["close"].ffill()   # carry last close into the gap
df["volume"] = df["volume"].fillna(0.0)  # volume = 0 for gap bars
```

### Why `freq="B"` (business days)?

`freq="B"` skips Saturday and Sunday automatically.
Without it, you'd get NaN rows for every weekend — then try to
fill them — creating thousands of fake "weekend bars" in your database.

With `freq="B"`, weekends don't exist in the full_range,
so `reindex` doesn't add NaN rows for them.
Only actual missing WEEKDAYS get filled.

### Why forward-fill and not backfill?

Forward-fill: Tuesday's price = Monday's close
→ The last confirmed price carried forward
→ This is what actually happened (price didn't change until market opened)

Backfill: Tuesday's price = Wednesday's open
→ Uses FUTURE data to fill the gap
→ **Look-ahead bias** — your strategy "knows" Wednesday's price on Tuesday
→ Backtest results will be wrong

---

## Step 3: keep="last" deduplication

```python
df.drop_duplicates(subset=["symbol", "timeframe", "timestamp"], keep="last")
```

If two rows have the same symbol+timeframe+timestamp:
- `keep="first"` → keep the older fetch (may be stale data)
- `keep="last"` → keep the newer fetch (more likely to be correct)

We use `keep="last"` because the pipeline may re-run after a partial
failure — the second run's data is typically more complete.

---

## Step 2: pd.to_numeric(errors="coerce")

```python
df["close"] = pd.to_numeric(df["close"], errors="coerce").astype(np.float64)
```

`errors="coerce"` is the key:
- `"raise"` → raises ValueError on any bad value (stops the pipeline)
- `"ignore"` → leaves bad values as-is (corrupts the data)
- `"coerce"` → converts bad values to NaN (we drop NaN in Step 6) ✅

This means: if Binance returns `"null"` instead of a number,
it becomes NaN → cleaned away in Step 6.
The pipeline continues. No crash.

---

## Gap-fill: daily only, not intraday

```python
if timeframe == "1d":
    df = self._fill_gaps(df)
# For "1h" and "15m": skip gap-fill
```

Why skip intraday?

A stock trades 9:15 AM to 3:30 PM IST (375 minutes).
In a 15-minute timeframe: 25 bars per day.
There are 23.75 hours of gaps per day (market closed).

If we filled those gaps:
- 25 real bars → 96 bars per day (24h × 4 per hour)
- 71 fake bars with `volume=0` and forward-filled prices
- Database grows 4x with meaningless data
- Intraday indicators (RSI-14 on 15m) would be completely wrong

For daily bars, a missing Tuesday is a data problem worth fixing.
For intraday bars, "missing" hours are just closed market — leave them.

---

## Tests we wrote today — 28 tests

```
TestCleanPipeline       3  — full pipeline smoke tests
TestNormaliseTimestamps 4  — tz-naive, UTC, IST, missing column
TestNormaliseDtypes     5  — strings, objects, missing volume
TestRemoveDuplicates    3  — exact dupes, keep="last", no dupes
TestFillGaps            6  — gap filled, price forward, zero volume, skip intraday
TestDropInvalid         5  — NaN, zero, negative, zero volume kept, all invalid
TestRealisticScenario   2  — messy input, sorted output
```

---

## Tomorrow — Day 24
PostgreSQL DB Writer with bulk upsert.
Takes the cleaned DataFrame and inserts rows into `price_bars`
using `ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING`.
Safe to run the pipeline any number of times — never duplicates.
