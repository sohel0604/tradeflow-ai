"""
TradeFlow AI — Data Cleaning Module
Day 23: Fix raw OHLCV data before it enters the database.

Raw data from yfinance and Binance has real-world problems:
  - Missing bars (market holidays, API gaps, weekend gaps)
  - Duplicate rows (pipeline ran twice, API returned overlap)
  - Wrong dtypes (strings instead of float64)
  - NaN values mid-series (corrupted data from the source)
  - Timezone-naive timestamps (must be UTC-aware)
  - Zero prices (data error — a stock can't trade at zero)

The cleaner fixes ALL of these before the DB writer inserts anything.

Pipeline flow:
  Fetcher → Cleaner → DB Writer → PostgreSQL
              ↑
          You are here
"""
from datetime import timezone

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)

# Expected pandas frequency alias per timeframe
# Used by pd.date_range to generate a "complete" time series
# so we can detect what's missing
TIMEFRAME_FREQ = {
    "1d":  "B",      # Business days (Mon-Fri, skips weekends)
    "1h":  "h",      # Every hour
    "15m": "15min",  # Every 15 minutes
}


class DataCleaner:
    """
    Cleans a raw OHLCV DataFrame before database insertion.

    All steps are applied in order via the clean() method.
    Each step is isolated — easy to test individually.
    """

    def clean(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Full cleaning pipeline. Call this after fetch(), before upsert().

        Args:
            df:        Raw DataFrame from any fetcher
            timeframe: "1d", "1h", or "15m"

        Returns:
            Cleaned DataFrame, empty if input is empty.
        """
        if df.empty:
            return df

        df = df.copy()
        symbol = df["symbol"].iloc[0] if "symbol" in df.columns else "unknown"
        rows_in = len(df)

        # Step 1 — Normalise timestamps to UTC timezone-aware
        df = self._normalise_timestamps(df)

        # Step 2 — Enforce float64 on all OHLCV columns
        df = self._normalise_dtypes(df)

        # Step 3 — Remove duplicate rows (same symbol+timeframe+timestamp)
        df = self._remove_duplicates(df)

        # Step 4 — Sort chronologically (required for gap-fill)
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Step 5 — Forward-fill missing bars in the time series
        #          (only applied to daily bars — intraday gaps are expected)
        if timeframe == "1d":
            df = self._fill_gaps(df)

        # Step 6 — Drop rows with invalid prices (zero, negative, NaN)
        df = self._drop_invalid(df)

        rows_out = len(df)
        logger.debug(
            "cleaning_complete",
            symbol=symbol,
            timeframe=timeframe,
            rows_in=rows_in,
            rows_out=rows_out,
            rows_dropped=rows_in - rows_out,
        )

        return df

    # -------------------------------------------------------------------------
    # Step 1: Normalise timestamps
    # -------------------------------------------------------------------------
    def _normalise_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure the 'timestamp' column is UTC timezone-aware.

        Handles three cases:
        1. timestamp column is already UTC-aware → leave alone
        2. timestamp column is tz-naive → localize to UTC
        3. timestamp column is a different timezone → convert to UTC
        """
        if "timestamp" not in df.columns:
            raise ValueError(
                "DataFrame has no 'timestamp' column. "
                "Did the fetcher run _normalise()?"
            )

        # Convert to datetime if it isn't already
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        if df["timestamp"].dt.tz is None:
            # tz-naive — assume UTC and localize
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        else:
            # tz-aware — convert to UTC (handles IST, EST etc.)
            df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")

        return df

    # -------------------------------------------------------------------------
    # Step 2: Normalise dtypes
    # -------------------------------------------------------------------------
    def _normalise_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enforce float64 on all OHLCV columns.

        yfinance sometimes returns object dtype (mixed types).
        Binance always returns strings that we already cast,
        but a second pass is free and safe.

        pd.to_numeric(..., errors="coerce") converts bad values to NaN
        instead of raising — we drop NaN rows in Step 6.
        """
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = (
                    pd.to_numeric(df[col], errors="coerce")
                    .astype(np.float64)
                )
            elif col == "volume":
                # Volume is optional — add as zeros if missing
                df["volume"] = np.float64(0.0)

        return df

    # -------------------------------------------------------------------------
    # Step 3: Remove duplicates
    # -------------------------------------------------------------------------
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows with duplicate (symbol, timeframe, timestamp) keys.

        When does this happen?
        - Pipeline runs twice on the same day
        - Binance pagination overlap (rare but possible)
        - CSV upload with duplicate rows

        keep="last" — if there are duplicates, keep the most recent one
        (the fetcher might have more accurate data on a second run).
        """
        key_cols = [c for c in ["symbol", "timeframe", "timestamp"]
                    if c in df.columns]

        before = len(df)
        df = df.drop_duplicates(subset=key_cols, keep="last")
        removed = before - len(df)

        if removed > 0:
            logger.debug("duplicates_removed", count=removed)

        return df.reset_index(drop=True)

    # -------------------------------------------------------------------------
    # Step 4: Sort (handled in clean() — not a separate method)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Step 5: Fill gaps (daily bars only)
    # -------------------------------------------------------------------------
    def _fill_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and forward-fill missing business-day bars.

        Example:
          Monday   close=100
          Tuesday  ← MISSING
          Wednesday close=102

          After fill:
          Monday   close=100
          Tuesday  close=100  ← copied from Monday (forward-fill)
          Wednesday close=102

        Why forward-fill and not interpolate?
        - Forward-fill is what really happened: price didn't change
          until the next traded candle
        - Interpolation would invent prices that never existed

        Why only daily?
        - Intraday (1h, 15m) gaps happen naturally during off-hours
          (market closed, crypto weekend low-volume etc.)
        - Forward-filling intraday gaps would create thousands of
          artificial candles and inflate our dataset

        We use "B" (business day) frequency which automatically
        skips Saturday and Sunday — no need to handle weekends manually.
        """
        if df.empty:
            return df

        try:
            # Set timestamp as the index for reindex
            df = df.set_index("timestamp")

            # Build a complete date range from first to last bar
            full_range = pd.date_range(
                start=df.index.min(),
                end=df.index.max(),
                freq=TIMEFRAME_FREQ["1d"],
                tz="UTC",
            )

            # Detect how many bars are missing
            missing_count = len(full_range.difference(df.index))

            if missing_count > 0:
                logger.debug("gaps_detected", count=missing_count)

                # Reindex to the full range — missing rows become NaN
                df = df.reindex(full_range)

                # Forward-fill OHLC (carry last known close into the gap)
                for col in ["open", "high", "low", "close"]:
                    if col in df.columns:
                        df[col] = df[col].ffill()

                # Volume of a gap bar = 0 (no trades happened)
                if "volume" in df.columns:
                    df["volume"] = df["volume"].fillna(0.0)

                # Forward-fill metadata columns
                for col in ["symbol", "timeframe", "asset_type"]:
                    if col in df.columns:
                        df[col] = df[col].ffill()

            # Restore timestamp as a column
            df = df.reset_index().rename(columns={"index": "timestamp"})

        except Exception as exc:
            # Gap-fill is best-effort — log and continue
            logger.warning("gap_fill_failed", error=str(exc))
            if "timestamp" not in df.columns:
                df = df.reset_index()

        return df

    # -------------------------------------------------------------------------
    # Step 6: Drop invalid rows
    # -------------------------------------------------------------------------
    def _drop_invalid(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows with:
        - NaN in any OHLC column (corrupted data)
        - Zero or negative prices (data error — impossible in real markets)

        Volume CAN be zero (gap-filled bars, forex) so we don't check it.
        """
        before = len(df)

        mask = (
            df["open"].notna()  & (df["open"]  > 0)
            & df["high"].notna() & (df["high"]  > 0)
            & df["low"].notna()  & (df["low"]   > 0)
            & df["close"].notna()& (df["close"] > 0)
        )

        df = df[mask].reset_index(drop=True)
        removed = before - len(df)

        if removed > 0:
            logger.debug("invalid_rows_dropped", count=removed)

        return df
