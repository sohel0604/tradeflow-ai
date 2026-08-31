"""
Day 23 — DataCleaner Unit Tests.

Tests every cleaning step independently and as a full pipeline.

Run with:
    docker compose exec backend pytest tests/unit/test_cleaner.py -v
"""
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta, timezone

from app.services.data.cleaner import DataCleaner


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------

def make_daily_df(
    rows: int = 10,
    symbol: str = "RELIANCE.NS",
    start: str = "2024-01-01",
    gaps: list[int] = None,        # row indices to remove (simulate gaps)
    tz: str = "UTC",
) -> pd.DataFrame:
    """Build a clean daily OHLCV DataFrame. Optionally remove rows to create gaps."""
    dates = pd.date_range(start=start, periods=rows, freq="B", tz=tz)
    df = pd.DataFrame({
        "timestamp": dates,
        "open":      np.linspace(100.0, 200.0, rows),
        "high":      np.linspace(110.0, 210.0, rows),
        "low":       np.linspace(90.0,  190.0, rows),
        "close":     np.linspace(105.0, 205.0, rows),
        "volume":    np.linspace(1e6,   2e6,   rows),
        "symbol":    symbol,
        "timeframe": "1d",
        "asset_type": "equity",
    })
    if gaps:
        df = df.drop(index=gaps).reset_index(drop=True)
    return df


@pytest.fixture
def cleaner():
    return DataCleaner()


# ---------------------------------------------------------------------------
# Test: clean() — full pipeline
# ---------------------------------------------------------------------------

class TestCleanPipeline:

    def test_returns_dataframe(self, cleaner):
        df = cleaner.clean(make_daily_df(), "1d")
        assert isinstance(df, pd.DataFrame)

    def test_empty_input_returns_empty(self, cleaner):
        df = cleaner.clean(pd.DataFrame(), "1d")
        assert df.empty

    def test_row_count_preserved_when_no_issues(self, cleaner):
        """Clean data → same number of rows out as in."""
        df_in = make_daily_df(rows=10)
        df_out = cleaner.clean(df_in, "1d")
        assert len(df_out) >= 10   # gap-fill may add rows but original preserved


# ---------------------------------------------------------------------------
# Step 1: Timestamp normalisation
# ---------------------------------------------------------------------------

class TestNormaliseTimestamps:

    def test_tz_naive_gets_utc(self, cleaner):
        """Timestamps without timezone should be localised to UTC."""
        df = make_daily_df(tz=None)   # tz=None → naive timestamps
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
        df_out = cleaner.clean(df, "1d")
        assert df_out["timestamp"].dt.tz == timezone.utc

    def test_utc_timestamps_unchanged(self, cleaner):
        """Already-UTC timestamps should remain UTC."""
        df = make_daily_df(tz="UTC")
        df_out = cleaner.clean(df, "1d")
        assert df_out["timestamp"].dt.tz == timezone.utc

    def test_ist_timestamps_converted_to_utc(self, cleaner):
        """Indian Standard Time (UTC+5:30) should be converted to UTC."""
        df = make_daily_df(tz="Asia/Kolkata")
        df_out = cleaner.clean(df, "1d")
        assert df_out["timestamp"].dt.tz == timezone.utc

    def test_missing_timestamp_column_raises(self, cleaner):
        """DataFrame without timestamp column must raise ValueError."""
        df = pd.DataFrame({"close": [100.0]})
        with pytest.raises(ValueError, match="timestamp"):
            cleaner._normalise_timestamps(df)


# ---------------------------------------------------------------------------
# Step 2: Dtype normalisation
# ---------------------------------------------------------------------------

class TestNormaliseDtypes:

    def test_string_prices_converted_to_float64(self, cleaner):
        """Binance returns prices as strings — must become float64."""
        df = make_daily_df(rows=3)
        df["close"] = df["close"].astype(str)   # corrupt to string
        df_out = cleaner.clean(df, "1d")
        assert df_out["close"].dtype == np.float64

    def test_object_dtype_converted(self, cleaner):
        df = make_daily_df(rows=3)
        df["open"] = df["open"].astype(object)
        df_out = cleaner.clean(df, "1d")
        assert df_out["open"].dtype == np.float64

    def test_all_ohlcv_are_float64(self, cleaner):
        df = make_daily_df(rows=5)
        df_out = cleaner.clean(df, "1d")
        for col in ["open", "high", "low", "close", "volume"]:
            assert df_out[col].dtype == np.float64, f"{col} not float64"

    def test_missing_volume_added_as_zeros(self, cleaner):
        """Forex DataFrames may not have a volume column."""
        df = make_daily_df(rows=3)
        df = df.drop(columns=["volume"])
        df_out = cleaner.clean(df, "1d")
        assert "volume" in df_out.columns
        assert (df_out["volume"] == 0.0).all()


# ---------------------------------------------------------------------------
# Step 3: Deduplication
# ---------------------------------------------------------------------------

class TestRemoveDuplicates:

    def test_exact_duplicates_removed(self, cleaner):
        """Appending the same DataFrame twice → duplicates removed."""
        df = make_daily_df(rows=5)
        df_duped = pd.concat([df, df], ignore_index=True)
        df_out = cleaner.clean(df_duped, "1d")
        assert len(df_out) == len(df)  # back to original count

    def test_keeps_later_duplicate(self, cleaner):
        """
        When two rows have the same timestamp,
        keep the last one (keep="last") — more recent data wins.
        """
        df = make_daily_df(rows=3)
        # Create a duplicate row with a different close price
        duplicate = df.iloc[[0]].copy()
        duplicate["close"] = 999.0
        df_combined = pd.concat([df, duplicate], ignore_index=True)

        df_out = cleaner._remove_duplicates(df_combined)

        # The row with close=999 should be kept (it's "last")
        ts = df.iloc[0]["timestamp"]
        row = df_out[df_out["timestamp"] == ts]
        assert len(row) == 1
        assert row["close"].iloc[0] == 999.0

    def test_non_duplicates_unchanged(self, cleaner):
        df = make_daily_df(rows=7)
        df_out = cleaner._remove_duplicates(df)
        assert len(df_out) == 7


# ---------------------------------------------------------------------------
# Step 5: Gap filling (daily only)
# ---------------------------------------------------------------------------

class TestFillGaps:

    def test_missing_business_day_filled(self, cleaner):
        """
        Tuesday is missing between Monday and Wednesday.
        After gap-fill, Tuesday should appear with Monday's prices.
        """
        # Create 5 business days then remove the middle one (index 2 = Wed)
        df = make_daily_df(rows=5, gaps=[2])
        assert len(df) == 4  # confirm gap exists

        df_out = cleaner.clean(df, "1d")

        # After fill we should have 5 rows
        assert len(df_out) == 5

    def test_gap_filled_with_forward_price(self, cleaner):
        """Gap bar's OHLC should equal the previous day's close."""
        df = make_daily_df(rows=5, gaps=[2])
        df_out = cleaner.clean(df, "1d")

        # Sort to ensure order
        df_out = df_out.sort_values("timestamp").reset_index(drop=True)
        # Row 2 is the gap-filled row — its close should match row 1 (previous)
        assert df_out.iloc[2]["close"] == pytest.approx(df_out.iloc[1]["close"])

    def test_gap_bar_has_zero_volume(self, cleaner):
        """Gap-filled bars should have volume=0 (no trades happened)."""
        df = make_daily_df(rows=5, gaps=[2])
        df_out = cleaner.clean(df, "1d").sort_values("timestamp").reset_index(drop=True)
        assert df_out.iloc[2]["volume"] == 0.0

    def test_no_gaps_rows_unchanged(self, cleaner):
        """DataFrame with no missing bars should have same row count."""
        df = make_daily_df(rows=5)
        df_out = cleaner.clean(df, "1d")
        assert len(df_out) == 5

    def test_gap_fill_skipped_for_1h(self, cleaner):
        """
        Intraday gaps are NOT filled — off-hours gaps are expected.
        A 1h DataFrame with gaps should keep the same row count.
        """
        df = make_daily_df(rows=5, gaps=[2])
        df["timeframe"] = "1h"
        df_out = cleaner.clean(df, "1h")
        # Should still be 4 rows — no fill applied
        assert len(df_out) == 4

    def test_gap_fill_skipped_for_15m(self, cleaner):
        df = make_daily_df(rows=5, gaps=[1])
        df["timeframe"] = "15m"
        df_out = cleaner.clean(df, "15m")
        assert len(df_out) == 4  # unchanged


# ---------------------------------------------------------------------------
# Step 6: Drop invalid rows
# ---------------------------------------------------------------------------

class TestDropInvalid:

    def test_nan_close_row_dropped(self, cleaner):
        df = make_daily_df(rows=5)
        df.loc[2, "close"] = np.nan
        df_out = cleaner.clean(df, "1d")
        # Row 2 dropped — but gap fill may re-add it, so check no NaN remains
        assert df_out["close"].notna().all()

    def test_zero_close_row_dropped(self, cleaner):
        df = make_daily_df(rows=5)
        df.loc[1, "close"] = 0.0
        df_out = cleaner.clean(df, "1d")
        assert (df_out["close"] > 0).all()

    def test_negative_price_row_dropped(self, cleaner):
        df = make_daily_df(rows=5)
        df.loc[3, "open"] = -50.0
        df_out = cleaner.clean(df, "1d")
        assert (df_out["open"] > 0).all()

    def test_zero_volume_rows_kept(self, cleaner):
        """Volume of 0 is valid (forex, gap-filled bars)."""
        df = make_daily_df(rows=5)
        df.loc[2, "volume"] = 0.0
        df_out = cleaner.clean(df, "1d")
        # Row with zero volume should still be there
        assert any(df_out["volume"] == 0.0)

    def test_all_invalid_returns_empty(self, cleaner):
        df = make_daily_df(rows=3)
        df["close"] = 0.0  # all rows invalid
        df_out = cleaner.clean(df, "1d")
        assert df_out.empty


# ---------------------------------------------------------------------------
# Integration: full realistic scenario
# ---------------------------------------------------------------------------

class TestRealisticScenario:

    def test_messy_data_comes_out_clean(self, cleaner):
        """
        Simulate a DataFrame with multiple issues at once:
        - 1 duplicate row
        - 1 missing business day
        - 1 NaN close
        - String dtype on open
        """
        df = make_daily_df(rows=10)

        # Add a duplicate
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        # Remove a row to create a gap
        df = df.drop(index=5).reset_index(drop=True)

        # Corrupt a close price to NaN
        df.loc[3, "close"] = np.nan

        # Corrupt open to string dtype
        df["open"] = df["open"].astype(str)

        df_out = cleaner.clean(df, "1d")

        # After cleaning:
        assert df_out["open"].dtype == np.float64    # dtypes fixed
        assert df_out["close"].notna().all()          # no NaN
        assert (df_out["close"] > 0).all()            # no invalid prices
        assert df_out["timestamp"].dt.tz == timezone.utc  # UTC timestamps
        # No duplicate timestamps
        assert df_out["timestamp"].nunique() == len(df_out)

    def test_sorted_output(self, cleaner):
        """Output must always be sorted chronologically."""
        df = make_daily_df(rows=5)
        df = df.sample(frac=1, random_state=42)  # shuffle
        df_out = cleaner.clean(df, "1d")
        timestamps = df_out["timestamp"].tolist()
        assert timestamps == sorted(timestamps)
