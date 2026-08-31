"""
Day 21 — yfinance Fetcher Unit Tests.

All tests mock yfinance.Ticker so they run:
  - Without internet connection
  - Without API keys
  - In milliseconds (no network call)

Run with:
    docker compose exec backend pytest tests/unit/test_yfinance_fetcher.py -v
"""
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.data.yfinance_fetcher import YFinanceFetcher
from app.services.data.base import REQUIRED_COLUMNS


# ---------------------------------------------------------------------------
# Helper: build a fake yfinance response DataFrame
# yfinance returns a DataFrame with DatetimeIndex + CamelCase columns
# ---------------------------------------------------------------------------
def make_yf_response(rows: int = 5, symbol: str = "RELIANCE.NS") -> pd.DataFrame:
    """Simulate what yfinance.Ticker.history() returns."""
    index = pd.date_range(
        start="2024-01-15",
        periods=rows,
        freq="B",       # business days
        tz="UTC",
    )
    return pd.DataFrame(
        {
            "Open":   np.linspace(2500.0, 2600.0, rows),
            "High":   np.linspace(2550.0, 2650.0, rows),
            "Low":    np.linspace(2450.0, 2550.0, rows),
            "Close":  np.linspace(2520.0, 2620.0, rows),
            "Volume": np.linspace(4000000, 5000000, rows),
        },
        index=index,
    )


@pytest.fixture
def fetcher():
    return YFinanceFetcher()


# ---------------------------------------------------------------------------
# Test: successful fetch
# ---------------------------------------------------------------------------
class TestFetchSuccess:

    @patch("yfinance.Ticker")
    def test_returns_dataframe(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = make_yf_response()
        df = fetcher.fetch("RELIANCE.NS", "1d", asset_type="equity")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    @patch("yfinance.Ticker")
    def test_has_all_required_columns(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = make_yf_response()
        df = fetcher.fetch("RELIANCE.NS", "1d", asset_type="equity")
        for col in REQUIRED_COLUMNS:
            assert col in df.columns, f"Missing column: {col}"

    @patch("yfinance.Ticker")
    def test_ohlcv_are_float64(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = make_yf_response()
        df = fetcher.fetch("RELIANCE.NS", "1d")
        for col in ["open", "high", "low", "close", "volume"]:
            assert df[col].dtype == np.float64, f"{col} is not float64"

    @patch("yfinance.Ticker")
    def test_symbol_uppercased(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = make_yf_response()
        df = fetcher.fetch("reliance.ns", "1d")
        assert (df["symbol"] == "RELIANCE.NS").all()

    @patch("yfinance.Ticker")
    def test_timestamps_are_utc(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = make_yf_response()
        df = fetcher.fetch("RELIANCE.NS", "1d")
        assert df["timestamp"].dt.tz == timezone.utc

    @patch("yfinance.Ticker")
    def test_asset_type_set_correctly(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = make_yf_response()
        df = fetcher.fetch("GC=F", "1d", asset_type="commodity")
        assert (df["asset_type"] == "commodity").all()

    @patch("yfinance.Ticker")
    def test_timeframe_set_correctly(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = make_yf_response()
        df = fetcher.fetch("AAPL", "1h", asset_type="equity")
        assert (df["timeframe"] == "1h").all()


# ---------------------------------------------------------------------------
# Test: forex — no volume column
# ---------------------------------------------------------------------------
class TestForexNoVolume:

    @patch("yfinance.Ticker")
    def test_volume_filled_with_zero(self, mock_ticker, fetcher):
        """
        Forex pairs don't have volume in yfinance.
        Our fetcher must add a volume column of zeros.
        """
        yf_resp = make_yf_response()
        yf_resp = yf_resp.drop(columns=["Volume"])  # simulate no volume

        mock_ticker.return_value.history.return_value = yf_resp
        df = fetcher.fetch("EURUSD=X", "1d", asset_type="forex")

        assert "volume" in df.columns
        assert (df["volume"] == 0.0).all()


# ---------------------------------------------------------------------------
# Test: failure cases — always return empty DataFrame, never raise
# ---------------------------------------------------------------------------
class TestFailureCases:

    @patch("yfinance.Ticker")
    def test_empty_response_returns_empty_df(self, mock_ticker, fetcher):
        """yfinance returns empty DataFrame for invalid symbols."""
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        df = fetcher.fetch("INVALID123", "1d")
        assert df.empty

    @patch("yfinance.Ticker")
    def test_network_error_returns_empty_df(self, mock_ticker, fetcher):
        """Network timeout must not crash the pipeline."""
        mock_ticker.return_value.history.side_effect = Exception("Connection timeout")
        df = fetcher.fetch("RELIANCE.NS", "1d")
        assert df.empty

    @patch("yfinance.Ticker")
    def test_unknown_error_returns_empty_df(self, mock_ticker, fetcher):
        """Any unexpected error must not crash the pipeline."""
        mock_ticker.return_value.history.side_effect = RuntimeError("Unexpected")
        df = fetcher.fetch("RELIANCE.NS", "1d")
        assert df.empty

    def test_invalid_timeframe_returns_empty_df(self, fetcher):
        """Invalid timeframe must return empty DataFrame."""
        df = fetcher.fetch("RELIANCE.NS", "5m")  # not a valid timeframe
        assert df.empty


# ---------------------------------------------------------------------------
# Test: normalisation
# ---------------------------------------------------------------------------
class TestNormalisation:

    @patch("yfinance.Ticker")
    def test_extra_columns_removed(self, mock_ticker, fetcher):
        """
        yfinance sometimes returns extra columns: Dividends, Stock Splits.
        Our normaliser must strip them.
        """
        yf_resp = make_yf_response()
        yf_resp["Dividends"] = 0.0
        yf_resp["Stock Splits"] = 0.0

        mock_ticker.return_value.history.return_value = yf_resp
        df = fetcher.fetch("TCS.NS", "1d")

        assert "dividends" not in df.columns
        assert "stock splits" not in df.columns

    @patch("yfinance.Ticker")
    def test_rows_with_nan_ohlc_dropped(self, mock_ticker, fetcher):
        """Rows with NaN OHLC values must be dropped."""
        yf_resp = make_yf_response(rows=5)
        yf_resp.iloc[2, yf_resp.columns.get_loc("Close")] = float("nan")

        mock_ticker.return_value.history.return_value = yf_resp
        df = fetcher.fetch("RELIANCE.NS", "1d")

        assert len(df) == 4  # row 2 dropped

    @patch("yfinance.Ticker")
    def test_index_reset(self, mock_ticker, fetcher):
        """Output DataFrame must have a clean 0-based integer index."""
        mock_ticker.return_value.history.return_value = make_yf_response()
        df = fetcher.fetch("RELIANCE.NS", "1d")
        assert list(df.index) == list(range(len(df)))


# ---------------------------------------------------------------------------
# Test: validate_symbol
# ---------------------------------------------------------------------------
class TestValidateSymbol:

    @patch("yfinance.Ticker")
    def test_valid_symbol_returns_true(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = make_yf_response(rows=3)
        assert fetcher.validate_symbol("RELIANCE.NS") is True

    @patch("yfinance.Ticker")
    def test_invalid_symbol_returns_false(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        assert fetcher.validate_symbol("NOTREAL123") is False

    @patch("yfinance.Ticker")
    def test_exception_returns_false(self, mock_ticker, fetcher):
        mock_ticker.return_value.history.side_effect = Exception("error")
        assert fetcher.validate_symbol("RELIANCE.NS") is False


# ---------------------------------------------------------------------------
# Test: symbol lists are populated
# ---------------------------------------------------------------------------
class TestSymbolLists:

    def test_indian_symbols_not_empty(self):
        from app.services.data.yfinance_fetcher import INDIAN_EQUITY_SYMBOLS
        assert len(INDIAN_EQUITY_SYMBOLS) >= 20

    def test_all_indian_symbols_have_ns_suffix_or_caret(self):
        from app.services.data.yfinance_fetcher import INDIAN_EQUITY_SYMBOLS
        for sym in INDIAN_EQUITY_SYMBOLS:
            assert sym.endswith(".NS") or sym.startswith("^"), \
                f"Indian symbol missing .NS suffix: {sym}"

    def test_forex_symbols_end_with_equals_x(self):
        from app.services.data.yfinance_fetcher import FOREX_SYMBOLS
        for sym in FOREX_SYMBOLS:
            assert sym.endswith("=X"), f"Forex symbol wrong format: {sym}"

    def test_commodity_symbols_end_with_equals_f(self):
        from app.services.data.yfinance_fetcher import COMMODITY_SYMBOLS
        for sym in COMMODITY_SYMBOLS:
            assert sym.endswith("=F"), f"Commodity symbol wrong format: {sym}"

    def test_all_yfinance_symbols_has_tuples(self):
        from app.services.data.yfinance_fetcher import ALL_YFINANCE_SYMBOLS
        for item in ALL_YFINANCE_SYMBOLS:
            assert isinstance(item, tuple), "Each item must be (symbol, asset_type)"
            assert len(item) == 2
            symbol, asset_type = item
            assert isinstance(symbol, str)
            assert asset_type in {"equity", "forex", "commodity"}
