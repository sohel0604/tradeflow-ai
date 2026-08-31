"""
TradeFlow AI — Base Data Fetcher Interface
Day 21: Abstract interface all fetchers must implement.

Why an interface?
- yfinance, Binance, Dhan all return data differently
- Our pipeline doesn't care WHERE the data came from
- Swap data sources without touching pipeline code
- Makes mocking in tests trivial

The contract:
  - fetch() always returns a standardised DataFrame
  - validate_symbol() checks if a symbol exists in this source
  - Never raises — returns empty DataFrame on any failure
"""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


# Columns every fetcher MUST return in its DataFrame
REQUIRED_COLUMNS = {
    "symbol",
    "timeframe",
    "timestamp",   # UTC timezone-aware datetime
    "open",        # float64
    "high",        # float64
    "low",         # float64
    "close",       # float64
    "volume",      # float64
    "asset_type",  # str: equity | crypto | forex | commodity | custom
}

# Valid timeframes across all sources
VALID_TIMEFRAMES = {"1d", "1h", "15m"}

# Valid asset types
VALID_ASSET_TYPES = {"equity", "crypto", "forex", "commodity", "custom"}


class BaseDataFetcher(ABC):
    """
    Abstract base class for all data fetchers.

    Rules all concrete fetchers must follow:
    1. fetch() returns a DataFrame with REQUIRED_COLUMNS
    2. fetch() NEVER raises — catches all errors, returns empty DataFrame
    3. All timestamps must be UTC timezone-aware
    4. All OHLCV columns must be float64
    5. validate_symbol() returns bool — True means the symbol exists
    """

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        asset_type: str = "equity",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV bars for a symbol.

        Args:
            symbol:     Ticker e.g. "RELIANCE.NS", "BTCUSDT", "EURUSD=X"
            timeframe:  "1d", "1h", or "15m"
            start:      Optional start date "YYYY-MM-DD"
            end:        Optional end date "YYYY-MM-DD"
            asset_type: One of VALID_ASSET_TYPES

        Returns:
            DataFrame with REQUIRED_COLUMNS, empty on any failure.
        """
        ...

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol exists in this data source.
        Used by the watchlist API before adding a symbol.
        Returns False on any error (network timeout etc.)
        """
        ...

    def _validate_output(self, df: pd.DataFrame) -> bool:
        """
        Verify the output DataFrame has all required columns.
        Used in tests to confirm fetcher output is correct.
        """
        if df.empty:
            return True  # Empty is valid — just means no data found
        missing = REQUIRED_COLUMNS - set(df.columns)
        return len(missing) == 0
