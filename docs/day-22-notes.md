# Day 22 Notes — August 25, 2026
## Topic: Binance REST API Fetcher — Crypto OHLCV

---

## Binance Public API — No Key Needed

Binance exposes market data without authentication:

```
GET https://api.binance.com/api/v3/klines
    ?symbol=BTCUSDT
    &interval=1d
    &limit=1000
    &startTime=1705276800000
```

Response — array of 12-element arrays:
```json
[
  [
    1705276800000,   // [0] open_time (milliseconds)
    "42150.00",      // [1] open
    "43200.00",      // [2] high
    "41800.00",      // [3] low
    "42900.50",      // [4] close
    "18750.50",      // [5] volume
    1705363199999,   // [6] close_time (ms)
    "...",           // [7-11] unused
  ]
]
```

We use fields [0]-[5] only.
Binance returns prices as STRINGS — we cast to float64.

---

## Milliseconds vs Seconds

Every timestamp-related bug with Binance comes from this:
Binance timestamps are in **milliseconds** not seconds.

```python
# WRONG — treats ms as seconds → year 56000
datetime.fromtimestamp(1705276800000)  # 😱

# CORRECT — divide by 1000 first
datetime.fromtimestamp(1705276800000 / 1000, tz=timezone.utc)
# → 2024-01-15 00:00:00 UTC ✅
```

Rule: whenever you see a Binance timestamp, divide by 1000.
When sending startTime/endTime to Binance, multiply by 1000.

---

## Pagination — fetching all historical data

Binance max limit per request = 1000 candles.
For 5 years of daily bars = 1825 candles = 2 requests.
For 2 years of hourly bars = 17520 candles = 18 requests.

The pagination loop:

```python
while True:
    params = {
        "symbol":    "BTCUSDT",
        "interval":  "1d",
        "limit":     1000,
        "startTime": start_ms,   # advance each loop
    }
    klines = GET("/klines", params)

    all_klines.extend(klines)

    if len(klines) < 1000:
        break  # last page — stop

    # Advance to after the last candle
    start_ms = klines[-1][0] + 1  # [0] = open_time

    time.sleep(0.1)  # respect rate limits
```

Key insight: `klines[-1][0]` is the open_time of the LAST candle.
We advance startTime to `last_open_time + 1ms` to get the next page.

---

## Rate limits — staying within Binance's rules

Binance allows 1200 requests/minute = 20 requests/second.
We sleep 0.1 seconds between requests = max 10 req/s.
Well within limits — never banned.

For 50 crypto symbols × 3 timeframes = 150 fetches.
At 0.1s sleep per page + ~1 page per fetch = ~15 seconds total.
Acceptable for a daily pipeline.

---

## requests.Session — connection reuse

```python
self.session = requests.Session()
```

Without Session: every request creates a new TCP connection.
With Session: TCP connection is reused across all requests.

For 150 paginated requests, this saves ~3-4 seconds
(each TCP handshake takes ~20ms).

---

## Mock testing strategy for HTTP APIs

```python
@patch("requests.Session.get")   # intercept all HTTP calls
def test_pagination(self, mock_get, fetcher):
    page1 = make_klines(1000)  # full page → triggers another request
    page2 = make_klines(50)    # partial page → stops

    mock_get.side_effect = [
        mock_response(page1),
        mock_response(page2),
    ]

    df = fetcher.fetch("BTCUSDT", "1d")

    assert len(df) == 1050
    assert mock_get.call_count == 2  # exactly 2 HTTP calls
```

`side_effect = [resp1, resp2]` — first call returns resp1,
second call returns resp2. Perfect for testing pagination.

`mock_get.call_count` — proves the fetcher made exactly 2 requests
(not 1, not 3). This level of precision is only possible with mocks.

---

## How the two fetchers compare

| | yfinance | Binance |
|--|---------|---------|
| **Data** | Stocks, Forex, Commodities | Crypto only |
| **Auth** | None | None |
| **Format** | DataFrame (DatetimeIndex) | List of 12-element arrays |
| **Pagination** | Handled internally | We handle manually |
| **Timestamps** | Already datetime | Milliseconds → convert |
| **Prices** | Already float | Strings → cast to float |
| **Output** | Same standard schema | Same standard schema |

Both return identical DataFrames after normalisation.
The pipeline can't tell them apart — that's the point of the interface.

---

## Tomorrow — Day 23
Data cleaning module.
Both fetchers return raw data with potential issues:
- Missing bars (market holidays, API gaps)
- Duplicate rows (if pipeline runs twice)
- Wrong dtypes (strings instead of floats)
- NaN values in the middle of a series

The cleaner fixes all of these before data reaches the DB.
