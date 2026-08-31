"""
Day 25 — Pipeline Task Unit Tests.

All external calls (yfinance, Binance, PostgreSQL) are mocked.
Tests verify task logic: correct calls made, correct return values,
correct error handling and log_fetch calls.

Run with:
    docker compose exec backend pytest tests/unit/test_pipeline_tasks.py -v
"""
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call


def make_clean_df(symbol="RELIANCE.NS", rows=5) -> pd.DataFrame:
    dates = pd.date_range("2024-01-15", periods=rows, freq="B", tz="UTC")
    return pd.DataFrame({
        "timestamp":  dates,
        "symbol":     symbol,
        "timeframe":  "1d",
        "open":       np.ones(rows) * 2500.0,
        "high":       np.ones(rows) * 2550.0,
        "low":        np.ones(rows) * 2450.0,
        "close":      np.ones(rows) * 2520.0,
        "volume":     np.ones(rows) * 4_000_000.0,
        "asset_type": "equity",
    })


# ---------------------------------------------------------------------------
# Test: fetch_yfinance_symbol
# ---------------------------------------------------------------------------

class TestFetchYfinanceSymbol:

    @patch("app.tasks.pipeline.log_fetch")
    @patch("app.tasks.pipeline.upsert_price_bars")
    @patch("app.tasks.pipeline._cleaner")
    @patch("app.tasks.pipeline._yfinance")
    def test_success_path(self, mock_yf, mock_cleaner,
                          mock_upsert, mock_log):
        """
        Happy path: fetch → clean → upsert → log SUCCESS
        """
        from app.tasks.pipeline import fetch_yfinance_symbol

        df = make_clean_df()
        mock_yf.fetch.return_value = df
        mock_cleaner.clean.return_value = df
        mock_upsert.return_value = 5

        result = fetch_yfinance_symbol.run("RELIANCE.NS", "equity", "1d")

        assert result["status"] == "SUCCESS"
        assert result["rows"]   == 5
        assert result["symbol"] == "RELIANCE.NS"

        # Verify correct calls were made in correct order
        mock_yf.fetch.assert_called_once_with(
            symbol="RELIANCE.NS",
            timeframe="1d",
            asset_type="equity",
        )
        mock_cleaner.clean.assert_called_once_with(df, "1d")
        mock_upsert.assert_called_once_with(df)
        mock_log.assert_called_once_with(
            "RELIANCE.NS", "1d", "SUCCESS", 5, source="yfinance"
        )

    @patch("app.tasks.pipeline.log_fetch")
    @patch("app.tasks.pipeline._yfinance")
    def test_empty_fetch_logs_failed(self, mock_yf, mock_log):
        """Empty response from yfinance → logs FAILED, returns FAILED status."""
        from app.tasks.pipeline import fetch_yfinance_symbol

        mock_yf.fetch.return_value = pd.DataFrame()

        result = fetch_yfinance_symbol.run("INVALID.NS", "equity", "1d")

        assert result["status"] == "FAILED"
        assert result["rows"]   == 0
        mock_log.assert_called_once()
        args = mock_log.call_args[0]
        assert args[2] == "FAILED"

    @patch("app.tasks.pipeline.log_fetch")
    @patch("app.tasks.pipeline.upsert_price_bars")
    @patch("app.tasks.pipeline._cleaner")
    @patch("app.tasks.pipeline._yfinance")
    def test_cleaner_returns_empty_logs_failed(self, mock_yf, mock_cleaner,
                                                mock_upsert, mock_log):
        """If cleaner drops all rows → FAILED, upsert never called."""
        from app.tasks.pipeline import fetch_yfinance_symbol

        mock_yf.fetch.return_value = make_clean_df()
        mock_cleaner.clean.return_value = pd.DataFrame()  # all dropped

        result = fetch_yfinance_symbol.run("RELIANCE.NS", "equity", "1d")

        assert result["status"] == "FAILED"
        mock_upsert.assert_not_called()  # should NOT reach upsert

    @patch("app.tasks.pipeline.log_fetch")
    @patch("app.tasks.pipeline.upsert_price_bars")
    @patch("app.tasks.pipeline._cleaner")
    @patch("app.tasks.pipeline._yfinance")
    def test_upsert_error_logs_failed_and_retries(self, mock_yf, mock_cleaner,
                                                   mock_upsert, mock_log):
        """
        If upsert raises an exception, the task should:
        1. Log FAILED with the error message
        2. Raise the exception (Celery will retry)
        """
        from app.tasks.pipeline import fetch_yfinance_symbol
        from celery.exceptions import Retry

        mock_yf.fetch.return_value    = make_clean_df()
        mock_cleaner.clean.return_value = make_clean_df()
        mock_upsert.side_effect       = Exception("DB connection lost")

        # Task should raise Retry (Celery's retry mechanism)
        with pytest.raises(Exception):
            fetch_yfinance_symbol.run("RELIANCE.NS", "equity", "1d")

        # Failure should be logged
        mock_log.assert_called_once()
        args = mock_log.call_args[0]
        assert args[2] == "FAILED"


# ---------------------------------------------------------------------------
# Test: fetch_binance_symbol
# ---------------------------------------------------------------------------

class TestFetchBinanceSymbol:

    @patch("app.tasks.pipeline.log_fetch")
    @patch("app.tasks.pipeline.upsert_price_bars")
    @patch("app.tasks.pipeline._cleaner")
    @patch("app.tasks.pipeline._binance")
    def test_success_path(self, mock_binance, mock_cleaner,
                          mock_upsert, mock_log):
        from app.tasks.pipeline import fetch_binance_symbol

        df = make_clean_df("BTCUSDT")
        df["asset_type"] = "crypto"
        mock_binance.fetch.return_value  = df
        mock_cleaner.clean.return_value  = df
        mock_upsert.return_value         = 5

        result = fetch_binance_symbol.run("BTCUSDT", "1d")

        assert result["status"] == "SUCCESS"
        assert result["symbol"] == "BTCUSDT"

        # Verify asset_type="crypto" is passed to Binance fetcher
        mock_binance.fetch.assert_called_once_with(
            symbol="BTCUSDT",
            timeframe="1d",
            asset_type="crypto",
        )
        mock_log.assert_called_once_with(
            "BTCUSDT", "1d", "SUCCESS", 5, source="binance"
        )

    @patch("app.tasks.pipeline.log_fetch")
    @patch("app.tasks.pipeline._binance")
    def test_empty_response_logs_failed(self, mock_binance, mock_log):
        from app.tasks.pipeline import fetch_binance_symbol

        mock_binance.fetch.return_value = pd.DataFrame()

        result = fetch_binance_symbol.run("FAKEPAIR", "1d")

        assert result["status"] == "FAILED"
        mock_log.assert_called_once()


# ---------------------------------------------------------------------------
# Test: run_full_pipeline
# ---------------------------------------------------------------------------

class TestRunFullPipeline:

    @patch("app.tasks.pipeline.group")
    def test_dispatches_tasks(self, mock_group):
        """
        run_full_pipeline should create a group and call apply_async().
        """
        from app.tasks.pipeline import run_full_pipeline

        mock_result      = MagicMock()
        mock_result.id   = "test-group-id-123"
        mock_group_instance = MagicMock()
        mock_group_instance.apply_async.return_value = mock_result
        mock_group.return_value = mock_group_instance

        result = run_full_pipeline.run()

        # Group was created
        mock_group.assert_called_once()
        # apply_async was called to dispatch tasks
        mock_group_instance.apply_async.assert_called_once()
        # Return value is correct
        assert result["status"]     == "dispatched"
        assert result["group_id"]   == "test-group-id-123"
        assert result["total_tasks"] > 0

    @patch("app.tasks.pipeline.group")
    def test_total_task_count_is_correct(self, mock_group):
        """
        Total tasks = (yfinance symbols + crypto symbols) × timeframes
        """
        from app.tasks.pipeline import (
            run_full_pipeline, ALL_YFINANCE_SYMBOLS,
            CRYPTO_SYMBOLS, TIMEFRAMES,
        )

        mock_group_instance = MagicMock()
        mock_group_instance.apply_async.return_value = MagicMock(id="x")
        mock_group.return_value = mock_group_instance

        run_full_pipeline.run()

        expected = (len(ALL_YFINANCE_SYMBOLS) + len(CRYPTO_SYMBOLS)) * len(TIMEFRAMES)

        # Extract the list passed to group()
        tasks_passed = mock_group.call_args[0][0]
        assert len(tasks_passed) == expected


# ---------------------------------------------------------------------------
# Test: task configuration
# ---------------------------------------------------------------------------

class TestTaskConfig:

    def test_yfinance_task_has_retry_config(self):
        from app.tasks.pipeline import fetch_yfinance_symbol
        assert fetch_yfinance_symbol.max_retries == 3

    def test_binance_task_has_retry_config(self):
        from app.tasks.pipeline import fetch_binance_symbol
        assert fetch_binance_symbol.max_retries == 3

    def test_pipeline_task_registered(self):
        """All tasks must be registered with Celery."""
        from app.celery_app import celery_app
        registered = list(celery_app.tasks.keys())
        assert "app.tasks.pipeline.fetch_yfinance_symbol" in registered
        assert "app.tasks.pipeline.fetch_binance_symbol"  in registered
        assert "app.tasks.pipeline.run_full_pipeline"     in registered

    def test_beat_schedule_configured(self):
        """Daily pipeline schedule must exist in Beat config."""
        from app.celery_app import celery_app
        schedules = celery_app.conf.beat_schedule
        assert "daily-pipeline-0630-IST" in schedules
        schedule  = schedules["daily-pipeline-0630-IST"]
        assert schedule["task"] == "app.tasks.pipeline.run_full_pipeline"
