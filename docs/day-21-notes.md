# Day 21 Notes — August 24, 2026
## Topic: yfinance Fetcher — Real Market Data

---

## What is yfinance?

yfinance is a Python library that downloads data from Yahoo Finance.
No API key. No registration. Completely free.

```python
import yfinance as yf

ticker = yf.Ticker("RELIANCE.NS")
df = ticker.history(period="1y", interval="1d")
print(df.head())
```

Output:
```
            Open    High     Low   Close    Volume
Date
2024-01-15  2500.0  2550.0  2450.0  2520.0  4000000
2024-01-16  2520.0  2570.0  2490.0  2545.0  3800000
...
```

That's real RELIANCE.NS stock data from NSE, downloaded in seconds.

---

## Ticker format reference

| Exchange | Format | Example |
|---------|--------|---------|
| NSE (India) | SYMBOL.NS | RELIANCE.NS |
| BSE (India) | SYMBOL.BO | RELIANCE.BO |
| NYSE/NASDAQ (US) | SYMBOL | AAPL, TSLA |
| Forex | XXXYYY=X | EURUSD=X |
| Commodities | SYM=F | GC=F (Gold) |
| Indices | ^INDEX | ^NSEI (NIFTY) |

---

## auto_adjust=True — why we always use it

```python
df = ticker.history(period="1y", auto_adjust=True)
```

Without `auto_adjust`:
- Prices are NOT adjusted for stock splits and dividends
- INFOSYS had a 1:2 split in 2021 — price halved overnight
- Your strategy sees a "crash" that never happened
- Your EMA, RSI calculations are wrong

With `auto_adjust=True`:
- All historical prices adjusted to reflect splits and dividends
- Prices look continuous — no artificial jumps
- Technical indicators compute correctly

Always use `auto_adjust=True` for backtesting.

---

## The _normalise() method — what it does

yfinance returns data in a specific format.
Our DB expects a different format.
`_normalise()` bridges the gap:

```
yfinance output:                Our standard schema:
─────────────────               ──────────────────────
DatetimeIndex (index)     →     timestamp column (UTC)
Open, High, Low, Close    →     open, high, low, close (float64)
Volume                    →     volume (float64, 0.0 if missing)
Dividends, Splits         →     DROPPED
(no symbol column)        →     symbol = "RELIANCE.NS"
(no timeframe column)     →     timeframe = "1d"
(no asset_type column)    →     asset_type = "equity"
```

After normalisation, every fetcher's output is identical.
The pipeline doesn't know if data came from yfinance or Binance.

---

## Error handling — never raise, always return empty

```python
try:
    df = ticker.history(...)
    return self._normalise(df, ...)
except Exception as exc:
    logger.error("yfinance_fetch_failed", error=str(exc))
    return pd.DataFrame()  # ← empty DataFrame, not an exception
```

Why return empty instead of raising?
The pipeline processes 50+ symbols in parallel.
If RELIANCE.NS fails (network timeout, Yahoo rate limit):
- With exception: entire pipeline crashes
- With empty DataFrame: RELIANCE.NS logs FAILED, other symbols continue

The Celery task catches the empty DataFrame and logs `status=FAILED`.
Other symbols in the group are unaffected.

---

## Unit testing with mocks — how @patch works

```python
@patch("yfinance.Ticker")      # replace yf.Ticker with a mock
def test_fetch(self, mock_ticker, fetcher):
    # Configure what the mock returns when .history() is called
    mock_ticker.return_value.history.return_value = make_yf_response()

    # Call the real fetcher — it calls the MOCK, not real Yahoo Finance
    df = fetcher.fetch("RELIANCE.NS", "1d")

    # Verify the output
    assert not df.empty
```

`@patch("yfinance.Ticker")` intercepts every `yf.Ticker()` call
in the module and replaces it with a `MagicMock`.

Benefits:
- Tests run in milliseconds (no network)
- Tests work offline (no internet needed)
- Tests are deterministic (no Yahoo Finance rate limits)
- Test data is exactly what you define

---

## make_yf_response() — the test helper

```python
def make_yf_response(rows=5) -> pd.DataFrame:
    index = pd.date_range("2024-01-15", periods=rows, freq="B", tz="UTC")
    return pd.DataFrame(
        {"Open": ..., "High": ..., "Low": ..., "Close": ..., "Volume": ...},
        index=index,
    )
```

This simulates exactly what `yf.Ticker.history()` returns.
`freq="B"` = business days (skips weekends, like real stock data).

---

## What the tests verify — 25 tests

```
TestFetchSuccess        → correct columns, types, timezone, symbol case
TestForexNoVolume       → volume=0.0 when forex has no volume
TestFailureCases        → empty response, network error, invalid timeframe
TestNormalisation       → extra columns removed, NaN rows dropped
TestValidateSymbol      → valid symbol True, invalid False
TestSymbolLists         → .NS suffix, =X format, =F format verified
```

---

## Tomorrow — Day 22
Binance REST API fetcher for cryptocurrency OHLCV data.
BTCUSDT, ETHUSDT, BNBUSDT.
Same interface as yfinance — same pipeline handles both.
