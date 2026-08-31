"""
Day 24 — DB Writer Integration Tests (requires real PostgreSQL).

These tests INSERT real rows into the database.
They use a unique test symbol "TESTSTOCK" so they don't
interfere with real data, and they clean up after themselves.

Run with:
    docker compose exec backend pytest tests/integration/test_db_writer_integration.py -v

IMPORTANT: Requires PostgreSQL to be running and migrations applied.
"""
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta, timezone

from app.services.data.db_writer import (
    upsert_price_bars,
    log_fetch,
    get_latest_timestamp,
    count_rows,
    get_sync_session,
)
from sqlalchemy import text

TEST_SYMBOL   = "TESTSTOCK"   # unique symbol — won't conflict with real data
TEST_SYMBOL_2 = "TESTSTOCK2"


def make_test_df(
    rows: int = 5,
    symbol: str = TEST_SYMBOL,
    start: str = "2024-01-15",
) -> pd.DataFrame:
    dates = pd.date_range(start=start, periods=rows, freq="B", tz="UTC")
    return pd.DataFrame({
        "timestamp":  dates,
        "symbol":     symbol,
        "timeframe":  "1d",
        "open":       np.linspace(100.0, 200.0, rows).astype(np.float64),
        "high":       np.linspace(110.0, 210.0, rows).astype(np.float64),
        "low":        np.linspace(90.0,  190.0, rows).astype(np.float64),
        "close":      np.linspace(105.0, 205.0, rows).astype(np.float64),
        "volume":     np.linspace(1e6,   2e6,   rows).astype(np.float64),
        "asset_type": "equity",
    })


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """
    Delete all test rows before AND after each test.
    autouse=True means this runs for every test automatically.
    """
    _delete_test_data()
    yield
    _delete_test_data()


def _delete_test_data():
    session = get_sync_session()
    try:
        session.execute(
            text("DELETE FROM price_bars WHERE symbol IN (:s1, :s2)"),
            {"s1": TEST_SYMBOL, "s2": TEST_SYMBOL_2},
        )
        session.execute(
            text("DELETE FROM fetch_logs WHERE symbol IN (:s1, :s2)"),
            {"s1": TEST_SYMBOL, "s2": TEST_SYMBOL_2},
        )
        session.commit()
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Test: upsert_price_bars
# ---------------------------------------------------------------------------

class TestUpsertPriceBars:

    def test_inserts_rows(self):
        """Basic insert — rows appear in the database."""
        df = make_test_df(rows=3)
        rows_saved = upsert_price_bars(df)
        assert rows_saved == 3

    def test_count_matches_after_insert(self):
        """count_rows() returns correct number after insert."""
        upsert_price_bars(make_test_df(rows=5))
        assert count_rows(TEST_SYMBOL, "1d") == 5

    def test_idempotent_second_insert(self):
        """
        Inserting the same data twice must NOT create duplicate rows.
        This is the core guarantee of ON CONFLICT DO NOTHING.
        """
        df = make_test_df(rows=4)
        upsert_price_bars(df)
        rows_second = upsert_price_bars(df)  # same data again

        # Second insert returns 0 (all rows skipped by conflict)
        assert rows_second == 0
        # Database still has exactly 4 rows (not 8)
        assert count_rows(TEST_SYMBOL, "1d") == 4

    def test_new_rows_added_existing_skipped(self):
        """
        Insert 3 rows. Then insert 5 rows (3 old + 2 new).
        Should insert 2 new, skip 3 existing.
        """
        upsert_price_bars(make_test_df(rows=3))
        upsert_price_bars(make_test_df(rows=5))  # 3 overlap + 2 new

        # Total should be 5 (not 8)
        assert count_rows(TEST_SYMBOL, "1d") == 5

    def test_empty_df_inserts_nothing(self):
        rows_saved = upsert_price_bars(pd.DataFrame())
        assert rows_saved == 0
        assert count_rows(TEST_SYMBOL, "1d") == 0

    def test_symbol_stored_uppercase(self):
        """Symbols must always be stored in uppercase."""
        df = make_test_df(rows=1)
        df["symbol"] = "teststock"   # lowercase input
        upsert_price_bars(df)
        # Query uppercase
        assert count_rows("TESTSTOCK", "1d") == 1

    def test_values_stored_correctly(self):
        """Verify the actual values in the database match the input."""
        df = make_test_df(rows=1)
        upsert_price_bars(df)

        session = get_sync_session()
        try:
            row = session.execute(
                text("""
                    SELECT open, high, low, close, volume, asset_type
                    FROM price_bars
                    WHERE symbol = :s AND timeframe = '1d'
                """),
                {"s": TEST_SYMBOL},
            ).fetchone()
        finally:
            session.close()

        assert row is not None
        assert abs(row.close  - float(df["close"].iloc[0]))  < 0.01
        assert abs(row.volume - float(df["volume"].iloc[0])) < 1.0
        assert row.asset_type == "equity"


# ---------------------------------------------------------------------------
# Test: log_fetch
# ---------------------------------------------------------------------------

class TestLogFetch:

    def test_success_logged(self):
        log_fetch(TEST_SYMBOL, "1d", "SUCCESS", rows_saved=10)
        session = get_sync_session()
        try:
            row = session.execute(
                text("SELECT status, rows_saved FROM fetch_logs WHERE symbol=:s"),
                {"s": TEST_SYMBOL},
            ).fetchone()
        finally:
            session.close()
        assert row.status == "SUCCESS"
        assert row.rows_saved == 10

    def test_failure_logged_with_error(self):
        log_fetch(TEST_SYMBOL, "1d", "FAILED", error_msg="Connection timeout")
        session = get_sync_session()
        try:
            row = session.execute(
                text("SELECT status, error_msg FROM fetch_logs WHERE symbol=:s"),
                {"s": TEST_SYMBOL},
            ).fetchone()
        finally:
            session.close()
        assert row.status == "FAILED"
        assert "timeout" in row.error_msg.lower()

    def test_multiple_logs_for_same_symbol(self):
        """Multiple fetch attempts create multiple log rows."""
        log_fetch(TEST_SYMBOL, "1d", "SUCCESS", rows_saved=5)
        log_fetch(TEST_SYMBOL, "1d", "SUCCESS", rows_saved=5)
        log_fetch(TEST_SYMBOL, "1d", "FAILED",  error_msg="error")

        session = get_sync_session()
        try:
            count = session.execute(
                text("SELECT COUNT(*) FROM fetch_logs WHERE symbol=:s"),
                {"s": TEST_SYMBOL},
            ).scalar()
        finally:
            session.close()
        assert count == 3


# ---------------------------------------------------------------------------
# Test: get_latest_timestamp
# ---------------------------------------------------------------------------

class TestGetLatestTimestamp:

    def test_returns_none_when_no_data(self):
        result = get_latest_timestamp(TEST_SYMBOL, "1d")
        assert result is None

    def test_returns_latest_after_insert(self):
        df = make_test_df(rows=5)
        upsert_price_bars(df)
        latest = get_latest_timestamp(TEST_SYMBOL, "1d")

        expected = df["timestamp"].max().to_pydatetime()
        # Compare without microseconds
        assert latest.date() == expected.date()

    def test_returns_most_recent_not_earliest(self):
        """Latest timestamp must be the LAST bar, not the first."""
        df = make_test_df(rows=5)
        upsert_price_bars(df)

        latest = get_latest_timestamp(TEST_SYMBOL, "1d")
        earliest = df["timestamp"].min().to_pydatetime()

        assert latest.date() != earliest.date()
        assert latest > earliest.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Test: pipeline simulation — fetch then upsert
# ---------------------------------------------------------------------------

class TestPipelineSimulation:

    def test_full_pipeline_flow(self):
        """
        Simulate a real pipeline run:
        1. Fetch data (mocked by make_test_df)
        2. Upsert into price_bars
        3. Log success to fetch_logs
        4. Verify everything is stored
        """
        df = make_test_df(rows=10)

        # Step 2: upsert
        rows_saved = upsert_price_bars(df)
        assert rows_saved == 10

        # Step 3: log success
        log_fetch(TEST_SYMBOL, "1d", "SUCCESS", rows_saved=rows_saved)

        # Step 4: verify
        assert count_rows(TEST_SYMBOL, "1d") == 10
        latest = get_latest_timestamp(TEST_SYMBOL, "1d")
        assert latest is not None

        # Verify fetch log exists
        session = get_sync_session()
        try:
            log = session.execute(
                text("SELECT status, rows_saved FROM fetch_logs WHERE symbol=:s"),
                {"s": TEST_SYMBOL},
            ).fetchone()
        finally:
            session.close()

        assert log.status == "SUCCESS"
        assert log.rows_saved == 10

    def test_incremental_fetch_pattern(self):
        """
        Day 1: insert 5 bars (Jan 15-19)
        Day 2: get latest, fetch from Jan 20 onwards, insert 3 more
        Total: 8 bars
        """
        # Day 1
        df1 = make_test_df(rows=5, start="2024-01-15")
        upsert_price_bars(df1)
        assert count_rows(TEST_SYMBOL, "1d") == 5

        # Get latest (simulates what the pipeline does before next fetch)
        latest = get_latest_timestamp(TEST_SYMBOL, "1d")
        assert latest is not None

        # Day 2 — fetch from day after latest
        next_start = (latest + timedelta(days=1)).strftime("%Y-%m-%d")
        df2 = make_test_df(rows=3, start=next_start)
        upsert_price_bars(df2)

        # Total: 5 + 3 = 8
        assert count_rows(TEST_SYMBOL, "1d") == 8
