"""
Day 24 — DB Writer Unit Tests (no database required).

Tests the _dataframe_to_records() helper and edge cases
that don't need a real PostgreSQL connection.

Run with:
    docker compose exec backend pytest tests/unit/test_db_writer.py -v
"""
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from app.services.data.db_writer import _dataframe_to_records


def make_clean_df(rows: int = 3) -> pd.DataFrame:
    """Minimal clean DataFrame matching our standard schema."""
    dates = pd.date_range("2024-01-15", periods=rows, freq="B", tz="UTC")
    return pd.DataFrame({
        "timestamp":  dates,
        "symbol":     "RELIANCE.NS",
        "timeframe":  "1d",
        "open":       np.linspace(2500.0, 2600.0, rows).astype(np.float64),
        "high":       np.linspace(2550.0, 2650.0, rows).astype(np.float64),
        "low":        np.linspace(2450.0, 2550.0, rows).astype(np.float64),
        "close":      np.linspace(2520.0, 2620.0, rows).astype(np.float64),
        "volume":     np.linspace(4e6,    5e6,    rows).astype(np.float64),
        "asset_type": "equity",
    })


class TestDataframeToRecords:

    def test_returns_list(self):
        records = _dataframe_to_records(make_clean_df())
        assert isinstance(records, list)

    def test_correct_row_count(self):
        records = _dataframe_to_records(make_clean_df(rows=5))
        assert len(records) == 5

    def test_empty_df_returns_empty_list(self):
        records = _dataframe_to_records(pd.DataFrame())
        assert records == []

    def test_each_record_has_required_keys(self):
        required = {"id", "symbol", "timeframe", "timestamp",
                    "open", "high", "low", "close", "volume",
                    "asset_type", "created_at"}
        for record in _dataframe_to_records(make_clean_df()):
            assert required.issubset(record.keys())

    def test_id_is_uuid(self):
        """Each row gets a unique UUID — not the same ID."""
        records = _dataframe_to_records(make_clean_df(3))
        ids = [r["id"] for r in records]
        assert len(set(ids)) == 3  # all unique

    def test_symbol_uppercased(self):
        df = make_clean_df()
        df["symbol"] = "reliance.ns"
        records = _dataframe_to_records(df)
        assert all(r["symbol"] == "RELIANCE.NS" for r in records)

    def test_numpy_float64_converted_to_python_float(self):
        """
        psycopg2 rejects numpy.float64 — must be plain Python float.
        This test proves the conversion happens.
        """
        records = _dataframe_to_records(make_clean_df())
        for r in records:
            assert type(r["open"])   is float
            assert type(r["close"])  is float
            assert type(r["volume"]) is float

    def test_timestamps_are_utc_aware_datetime(self):
        """SQLAlchemy needs Python datetime objects, not pandas Timestamps."""
        records = _dataframe_to_records(make_clean_df())
        for r in records:
            ts = r["timestamp"]
            assert isinstance(ts, datetime)
            assert ts.tzinfo is not None
            assert ts.tzinfo == timezone.utc

    def test_tz_naive_timestamp_gets_utc(self):
        """Timezone-naive timestamps should be localised to UTC."""
        df = make_clean_df()
        # Strip timezone from timestamps
        df["timestamp"] = df["timestamp"].dt.tz_localize(None)
        records = _dataframe_to_records(df)
        for r in records:
            assert r["timestamp"].tzinfo == timezone.utc

    def test_missing_volume_defaults_to_zero(self):
        """If volume column absent, default to 0.0."""
        df = make_clean_df().drop(columns=["volume"])
        records = _dataframe_to_records(df)
        assert all(r["volume"] == 0.0 for r in records)

    def test_missing_asset_type_defaults_to_equity(self):
        df = make_clean_df().drop(columns=["asset_type"])
        records = _dataframe_to_records(df)
        assert all(r["asset_type"] == "equity" for r in records)

    def test_created_at_is_recent_utc(self):
        """created_at should be close to now (within a few seconds)."""
        records = _dataframe_to_records(make_clean_df())
        now = datetime.now(timezone.utc)
        for r in records:
            diff = abs((now - r["created_at"]).total_seconds())
            assert diff < 5, f"created_at is too old: {diff}s ago"


class TestRecordValues:

    def test_ohlcv_values_match_input(self):
        df = make_clean_df(rows=1)
        records = _dataframe_to_records(df)
        r = records[0]

        assert r["open"]   == pytest.approx(float(df["open"].iloc[0]))
        assert r["high"]   == pytest.approx(float(df["high"].iloc[0]))
        assert r["low"]    == pytest.approx(float(df["low"].iloc[0]))
        assert r["close"]  == pytest.approx(float(df["close"].iloc[0]))
        assert r["volume"] == pytest.approx(float(df["volume"].iloc[0]))

    def test_timestamp_value_matches_input(self):
        df = make_clean_df(rows=1)
        records = _dataframe_to_records(df)
        expected = pd.Timestamp("2024-01-15", tz="UTC").to_pydatetime()
        assert records[0]["timestamp"] == expected

    def test_all_ids_are_valid_uuids(self):
        records = _dataframe_to_records(make_clean_df(rows=5))
        for r in records:
            # Should not raise
            uuid.UUID(str(r["id"]))
