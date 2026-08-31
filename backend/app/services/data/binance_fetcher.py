"""
TradeFlow AI — Binance REST API Fetcher
Day 22: Download OHLCV data for cryptocurrencies.

Why Binance?
- Largest crypto exchange by volume
- Public REST API — no API key required for market data
- Deep historical data (years of daily, hourly, 15m bars)
- Reliable uptime and fast response times

Binance API endpoints used:
  GET https://api.binance.com/api/v3/klines
  GET https://api.binance.com/api/v3/exchangeInfo  (symbol validation)

Kline response format (12 fields per candle):
  [0]  open_time       (milliseconds since Unix epoch)
  [1]  open            (string)
  [2]  high            (string)
  [3]  low             (string)
  [4]  close           (string)
  [5]  volume          (string)
  [6]  close_time      (ms)
  [7]  quote_volume    (string) — we don't use this
  [8]  trades          (int)    — we don't use this
  [9]  taker_buy_base  (string) — we don't use this
  [10] taker_buy_quote (string) — we don't use this
  [11] ignore          (string)

Pagination:
  Binance returns max 1000 candles per request.
  For years of daily bars we need multiple requests.
  We advance startTime after each page until we've fetched all data.
"""
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
import pandas as pd
import requests
import structlog

from app.services.data.base import BaseDataFetcher

logger = structlog.get_logger(__name__)

BINANCE_BASE_URL = "https://api.binance.com/api/v3"
BINANCE_MAX_LIMIT = 1000   # max candles Binance returns per request
REQUEST_TIMEOUT  = 30      # seconds

# Map our timeframe names to Binance interval strings
INTERVAL_MAP = {
    "1d":  "1d",
    "1h":  "1h",
    "15m": "15m",
}

# How far back to fetch if no start date given
DEFAULT_LOOKBACK = {
    "1d":  365 * 5,   # 5 years of daily bars
    "1h":  365 * 2,   # 2 years of hourly bars
    "15m": 60,        # 60 days of 15-min bars
}


class BinanceFetcher(BaseDataFetcher):
    """
    Fetches OHLCV data from the Binance public REST API.
    No API key required.
    """

    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        # Reuse one session for all requests — avoids TCP handshake overhead
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.timeout = timeout

    def fetch(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        asset_type: str = "crypto",
    ) -> pd.DataFrame:
        """
        Download OHLCV klines from Binance.

        Returns empty DataFrame on any error — never raises.
        """
        interval = INTERVAL_MAP.get(timeframe)
        if not interval:
            logger.warning("binance_invalid_timeframe", timeframe=timeframe)
            return pd.DataFrame()

        symbol_upper = symbol.upper()

        try:
            klines = self._fetch_all_klines(
                symbol=symbol_upper,
                interval=interval,
                timeframe=timeframe,
                start=start,
                end=end,
            )

            if not klines:
                logger.warning(
                    "binance_empty_response",
                    symbol=symbol_upper,
                    timeframe=timeframe,
                )
                return pd.DataFrame()

            df = self._klines_to_dataframe(klines, symbol_upper, timeframe, asset_type)

            logger.info(
                "binance_fetch_success",
                symbol=symbol_upper,
                timeframe=timeframe,
                rows=len(df),
            )
            return df

        except Exception as exc:
            logger.error(
                "binance_fetch_failed",
                symbol=symbol_upper,
                timeframe=timeframe,
                error=str(exc),
            )
            return pd.DataFrame()

    def _fetch_all_klines(
        self,
        symbol: str,
        interval: str,
        timeframe: str,
        start: Optional[str],
        end: Optional[str],
    ) -> list:
        """
        Paginate through the Binance klines endpoint.

        Binance returns max 1000 candles per request.
        We keep advancing startTime until we get all candles.

        Returns list of raw kline arrays.
        """
        all_klines: list = []

        # Convert start date to milliseconds (Binance uses ms timestamps)
        if start:
            start_ms = int(
                datetime.strptime(start, "%Y-%m-%d")
                .replace(tzinfo=timezone.utc)
                .timestamp() * 1000
            )
        else:
            # Default: look back N days from now
            lookback_days = DEFAULT_LOOKBACK[timeframe]
            start_ms = int(
                (datetime.now(timezone.utc) - timedelta(days=lookback_days))
                .timestamp() * 1000
            )

        # Convert end date to milliseconds
        end_ms: Optional[int] = None
        if end:
            end_ms = int(
                datetime.strptime(end, "%Y-%m-%d")
                .replace(tzinfo=timezone.utc)
                .timestamp() * 1000
            )

        while True:
            params = {
                "symbol":    symbol,
                "interval":  interval,
                "limit":     BINANCE_MAX_LIMIT,
                "startTime": start_ms,
            }
            if end_ms:
                params["endTime"] = end_ms

            resp = self.session.get(
                f"{BINANCE_BASE_URL}/klines",
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            klines = resp.json()

            if not klines:
                break   # no more data

            all_klines.extend(klines)

            # If we got fewer than the limit, we've reached the end
            if len(klines) < BINANCE_MAX_LIMIT:
                break

            # Advance startTime to the millisecond AFTER the last candle
            # klines[-1][0] is the open_time of the last candle
            last_open_time_ms = klines[-1][0]
            start_ms = last_open_time_ms + 1

            # Respect Binance rate limits (1200 requests/min)
            # 0.1s between requests = max 10 req/s = well within limits
            time.sleep(0.1)

        return all_klines

    def _klines_to_dataframe(
        self,
        klines: list,
        symbol: str,
        timeframe: str,
        asset_type: str,
    ) -> pd.DataFrame:
        """
        Convert Binance kline list to our standard DataFrame schema.

        Binance kline[0] is the open_time in milliseconds.
        Divide by 1000 to get seconds, then convert to UTC datetime.

        Binance returns OHLCV as strings — we cast to float64.
        """
        rows = []
        for k in klines:
            rows.append({
                "timestamp": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                "open":      float(k[1]),
                "high":      float(k[2]),
                "low":       float(k[3]),
                "close":     float(k[4]),
                "volume":    float(k[5]),
            })

        df = pd.DataFrame(rows)

        # Enforce float64
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(np.float64)

        # Add metadata
        df["symbol"]     = symbol
        df["timeframe"]  = timeframe
        df["asset_type"] = asset_type

        # Drop NaN rows (shouldn't happen but defensive)
        df = df.dropna(subset=["open", "high", "low", "close"])

        return df.reset_index(drop=True)

    def validate_symbol(self, symbol: str) -> bool:
        """
        Check if a Binance symbol exists by requesting 1 candle.
        Returns False for invalid symbols or network errors.
        """
        try:
            resp = self.session.get(
                f"{BINANCE_BASE_URL}/klines",
                params={
                    "symbol":   symbol.upper(),
                    "interval": "1d",
                    "limit":    1,
                },
                timeout=self.timeout,
            )
            # 400 = invalid symbol, 200 = valid
            return resp.status_code == 200 and bool(resp.json())
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Default crypto symbols for the daily pipeline
# ---------------------------------------------------------------------------

CRYPTO_SYMBOLS = [
    "BTCUSDT",   # Bitcoin
    "ETHUSDT",   # Ethereum
    "BNBUSDT",   # Binance Coin
    "SOLUSDT",   # Solana
    "ADAUSDT",   # Cardano
    "XRPUSDT",   # Ripple
    "DOGEUSDT",  # Dogecoin
    "AVAXUSDT",  # Avalanche
    "DOTUSDT",   # Polkadot
    "MATICUSDT", # Polygon
]
