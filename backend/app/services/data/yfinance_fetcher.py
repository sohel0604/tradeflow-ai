"""
TradeFlow AI — yfinance Data Fetcher
Day 21: Download OHLCV data for equities, forex, commodities.

yfinance is a Python library that scrapes Yahoo Finance.
No API key required. Completely free.

Ticker formats:
  Indian equities:  RELIANCE.NS, TCS.NS, INFY.NS  (.NS = NSE)
  US equities:      AAPL, TSLA, NVDA
  Forex:            EURUSD=X, USDINR=X, GBPUSD=X
  Commodities:      GC=F (Gold), CL=F (Crude Oil), SI=F (Silver)
  Indices:          ^NSEI (NIFTY 50), ^BSESN (SENSEX)

Intraday limits (Yahoo Finance restriction):
  1h  → max 730 days of history
  15m → max 60 days of history
  1d  → max 5 years of history
"""
from typing import Optional

import numpy as np
import pandas as pd
import structlog
import yfinance as yf

from app.services.data.base import BaseDataFetcher

logger = structlog.get_logger(__name__)

# Map our timeframe names to yfinance interval strings
INTERVAL_MAP = {
    "1d":  "1d",
    "1h":  "1h",
    "15m": "15m",
}

# Maximum history yfinance allows per timeframe
# Requesting more than this returns an empty DataFrame
PERIOD_LIMIT = {
    "1d":  "5y",   # 5 years of daily bars
    "1h":  "730d", # 2 years of hourly bars
    "15m": "60d",  # 60 days of 15-minute bars
}


class YFinanceFetcher(BaseDataFetcher):
    """
    Fetches OHLCV data from Yahoo Finance via the yfinance library.
    No API key required.
    """

    def fetch(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        asset_type: str = "equity",
    ) -> pd.DataFrame:
        """
        Download OHLCV bars from Yahoo Finance.

        Returns empty DataFrame on any error — never raises.
        The caller (Celery task) logs the failure separately.
        """
        interval = INTERVAL_MAP.get(timeframe)
        if not interval:
            logger.warning("invalid_timeframe", timeframe=timeframe)
            return pd.DataFrame()

        try:
            ticker = yf.Ticker(symbol)

            # Use date range if provided, otherwise use period limit
            if start and end:
                df = ticker.history(
                    start=start,
                    end=end,
                    interval=interval,
                    auto_adjust=True,  # adjusts for splits and dividends
                )
            else:
                period = PERIOD_LIMIT[timeframe]
                df = ticker.history(
                    period=period,
                    interval=interval,
                    auto_adjust=True,
                )

            if df.empty:
                logger.warning(
                    "yfinance_empty_response",
                    symbol=symbol,
                    timeframe=timeframe,
                )
                return pd.DataFrame()

            df = self._normalise(df, symbol, timeframe, asset_type)

            logger.info(
                "yfinance_fetch_success",
                symbol=symbol,
                timeframe=timeframe,
                rows=len(df),
            )
            return df

        except Exception as exc:
            logger.error(
                "yfinance_fetch_failed",
                symbol=symbol,
                timeframe=timeframe,
                error=str(exc),
            )
            return pd.DataFrame()

    def _normalise(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        asset_type: str,
    ) -> pd.DataFrame:
        """
        Convert yfinance output into our standard schema.

        yfinance returns:
          - CamelCase column names: Open, High, Low, Close, Volume
          - DatetimeIndex as the index
          - May include extra columns: Dividends, Stock Splits

        We return:
          - Lowercase columns: open, high, low, close, volume
          - A 'timestamp' column (not index)
          - All OHLCV as float64
          - Timestamps as UTC timezone-aware datetime
          - Metadata columns: symbol, timeframe, asset_type
        """
        df = df.copy()

        # Step 1: lowercase all column names
        df.columns = [c.lower() for c in df.columns]

        # Step 2: keep only OHLCV columns (drop dividends, splits etc.)
        keep = ["open", "high", "low", "close", "volume"]
        df = df[[c for c in keep if c in df.columns]]

        # Step 3: add missing volume column (forex has no volume)
        if "volume" not in df.columns:
            df["volume"] = 0.0

        # Step 4: enforce float64 on all numeric columns
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(np.float64)

        # Step 5: convert DatetimeIndex to UTC timezone-aware column
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        df["timestamp"] = df.index

        # Step 6: add metadata columns
        df["symbol"]     = symbol.upper()
        df["timeframe"]  = timeframe
        df["asset_type"] = asset_type

        # Step 7: drop rows with NaN OHLC (bad data)
        df = df.dropna(subset=["open", "high", "low", "close"])

        return df.reset_index(drop=True)

    def validate_symbol(self, symbol: str) -> bool:
        """
        Check if a yfinance symbol returns any data.
        Used by watchlist API before adding a symbol.
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d", interval="1d")
            return not df.empty
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Default symbol lists used by the daily pipeline
# ---------------------------------------------------------------------------

INDIAN_EQUITY_SYMBOLS = [
    "RELIANCE.NS",   # Reliance Industries
    "TCS.NS",        # Tata Consultancy Services
    "HDFCBANK.NS",   # HDFC Bank
    "INFY.NS",       # Infosys
    "ICICIBANK.NS",  # ICICI Bank
    "HINDUNILVR.NS", # Hindustan Unilever
    "SBIN.NS",       # State Bank of India
    "BHARTIARTL.NS", # Bharti Airtel
    "ITC.NS",        # ITC Limited
    "KOTAKBANK.NS",  # Kotak Mahindra Bank
    "LT.NS",         # Larsen & Toubro
    "AXISBANK.NS",   # Axis Bank
    "ASIANPAINT.NS", # Asian Paints
    "MARUTI.NS",     # Maruti Suzuki
    "BAJFINANCE.NS", # Bajaj Finance
    "WIPRO.NS",      # Wipro
    "ULTRACEMCO.NS", # UltraTech Cement
    "TITAN.NS",      # Titan Company
    "SUNPHARMA.NS",  # Sun Pharmaceutical
    "NESTLEIND.NS",  # Nestlé India
    "^NSEI",         # NIFTY 50 index
    "^BSESN",        # SENSEX index
]

US_EQUITY_SYMBOLS = [
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "GOOGL",  # Alphabet
    "AMZN",   # Amazon
    "NVDA",   # NVIDIA
    "TSLA",   # Tesla
    "META",   # Meta
    "NFLX",   # Netflix
    "AMD",    # AMD
    "INTC",   # Intel
]

FOREX_SYMBOLS = [
    "EURUSD=X",  # Euro / US Dollar
    "GBPUSD=X",  # British Pound / US Dollar
    "USDINR=X",  # US Dollar / Indian Rupee
    "USDJPY=X",  # US Dollar / Japanese Yen
    "AUDUSD=X",  # Australian Dollar / US Dollar
    "USDCAD=X",  # US Dollar / Canadian Dollar
]

COMMODITY_SYMBOLS = [
    "GC=F",  # Gold futures
    "SI=F",  # Silver futures
    "CL=F",  # Crude Oil WTI futures
    "NG=F",  # Natural Gas futures
]

# Combined list with asset types — used by the Celery pipeline
ALL_YFINANCE_SYMBOLS: list[tuple[str, str]] = (
    [(s, "equity")    for s in INDIAN_EQUITY_SYMBOLS]
    + [(s, "equity")  for s in US_EQUITY_SYMBOLS]
    + [(s, "forex")   for s in FOREX_SYMBOLS]
    + [(s, "commodity") for s in COMMODITY_SYMBOLS]
)
