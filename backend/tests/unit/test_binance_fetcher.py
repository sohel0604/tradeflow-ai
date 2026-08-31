"""
Day 22 — Binance Fetcher Unit Tests.

All network calls are mocked — tests run offline in milliseconds.

Run with:
    docker compose exec backend pytest tests/unit/test_binance_fetcher.py -v
"""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.services.data.binance_fetcher import BinanceFetcher
from app.services.data.base import REQUIRED_COLUMNS


# ---------------------------------------------------------------------------
# Helpers — build fake Binance kline responses
# ---------------------------------------------------------------------------

def make_kline(open_time_ms: int, price: float = 42000.0) -> list:
    """
    One Binance kline — the 12-element list format Binance returns.
    Index 0=open_time, 1=open, 2=high, 3=low, 4=close, 5=volume
    """
    return [
        open_time_ms,         # [0] open_time ms
        str(price),           # [1] open
        str(price + 500),     # [2] high
        str(price - 500),     # [3] low
        str(price + 100),     # [4] close
        "18750.5",            # [5] volume
        open_time_ms + 86399999, # [6] close_time ms
        "0",                  # [7] quote_volume
        1000,                 # [8] trades
        "0", "0", "0",        # [9-11] unused
    ]


def make_klines(count: int, start_ms: int = 1705276800000) -> list:
    """
    Build a list of N klines starting from start_ms.
    Each candle is 1 day apart (86_400_000 ms).
    """
    return [
        make_kline(start_ms + i * 86_400_000, price=42000.0 + i * 100)
        for i in range(count)
    ]


def mock_response(klines: list, status_code: int = 200) -> MagicMock:
    """Build a mock requests.Response object."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = klines
    resp.raise_for_status = MagicMock()  # no-op
    return resp


@pytest.fixture
def fetcher():
    return BinanceFetcher()


# ---------------------------------------------------------------------------
# Test: successful fetch
# ---------------------------------------------------------------------------

class TestFetchSuccess:

    @patch("requests.Session.get")
    def test_returns_dataframe(self, mock_get, fetcher):
        mock_get.return_value = mock_response(make_klines(5))
        df = fetcher.fetch("BTCUSDT", "1d")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    @patch("requests.Session.get")
    def test_has_all_required_columns(self, mock_get, fetcher):
        mock_get.return_value = mock_response(make_klines(5))
        df = fetcher.fetch("BTCUSDT", "1d")
        for col in REQUIRED_COLUMNS:
            assert col in df.columns, f"Missing column: {col}"

    @patch("requests.Session.get")
    def test_ohlcv_are_float64(self, mock_get, fetcher):
        mock_get.return_value = mock_response(make_klines(5))
        df = fetcher.fetch("BTCUSDT", "1d")
        for col in ["open", "high", "low", "close", "volume"]:
            assert df[col].dtype == np.float64, f"{col} not float64"

    @patch("requests.Session.get")
    def test_symbol_uppercased(self, mock_get, fetcher):
        mock_get.return_value = mock_response(make_klines(3))
        df = fetcher.fetch("btcusdt", "1d")
        assert (df["symbol"] == "BTCUSDT").all()

    @patch("requests.Session.get")
    def test_asset_type_is_crypto(self, mock_get, fetcher):
        mock_get.return_value = mock_response(make_klines(3))
        df = fetcher.fetch("BTCUSDT", "1d", asset_type="crypto")
        assert (df["asset_type"] == "crypto").all()

    @patch("requests.Session.get")
    def test_timestamps_are_utc(self, mock_get, fetcher):
        mock_get.return_value = mock_response(make_klines(3))
        df = fetcher.fetch("BTCUSDT", "1d")
        assert df["timestamp"].dt.tz == timezone.utc

    @patch("requests.Session.get")
    def test_open_time_converted_from_ms_correctly(self, mock_get, fetcher):
        """
        Binance uses milliseconds. We convert to UTC datetime.
        1705276800000 ms = 2024-01-15 00:00:00 UTC
        """
        start_ms = 1705276800000  # 2024-01-15 00:00:00 UTC
        mock_get.return_value = mock_response([make_kline(start_ms)])

        df = fetcher.fetch("BTCUSDT", "1d")

        expected = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        assert df["timestamp"].iloc[0] == expected

    @patch("requests.Session.get")
    def test_ohlcv_values_correct(self, mock_get, fetcher):
        """Verify OHLCV values from kline[1-5] are parsed correctly."""
        kline = make_kline(1705276800000, price=42000.0)
        mock_get.return_value = mock_response([kline])

        df = fetcher.fetch("BTCUSDT", "1d")

        assert df["open"].iloc[0]   == 42000.0
        assert df["high"].iloc[0]   == 42500.0  # price + 500
        assert df["low"].iloc[0]    == 41500.0  # price - 500
        assert df["close"].iloc[0]  == 42100.0  # price + 100
        assert df["volume"].iloc[0] == 18750.5


# ---------------------------------------------------------------------------
# Test: pagination — multiple pages of data
# ---------------------------------------------------------------------------

class TestPagination:

    @patch("requests.Session.get")
    def test_fetches_multiple_pages(self, mock_get, fetcher):
        """
        When first page returns 1000 klines (the limit),
        the fetcher must request another page.
        Second page returns fewer → stop.
        """
        page1 = make_klines(1000, start_ms=1000000000000)
        page2 = make_klines(50, start_ms=1000000000000 + 1000 * 86_400_000)

        # First call returns full page, second returns partial
        mock_get.side_effect = [
            mock_response(page1),
            mock_response(page2),
        ]

        df = fetcher.fetch("BTCUSDT", "1d")

        assert len(df) == 1050          # 1000 + 50
        assert mock_get.call_count == 2  # exactly 2 HTTP requests

    @patch("requests.Session.get")
    def test_single_page_no_second_request(self, mock_get, fetcher):
        """When first page has < 1000 klines, only one request is made."""
        mock_get.return_value = mock_response(make_klines(250))
        df = fetcher.fetch("BTCUSDT", "1d")

        assert len(df) == 250
        assert mock_get.call_count == 1


# ---------------------------------------------------------------------------
# Test: failure cases — always return empty, never raise
# ---------------------------------------------------------------------------

class TestFailureCases:

    @patch("requests.Session.get")
    def test_empty_response_returns_empty_df(self, mock_get, fetcher):
        mock_get.return_value = mock_response([])
        df = fetcher.fetch("BTCUSDT", "1d")
        assert df.empty

    @patch("requests.Session.get")
    def test_network_error_returns_empty_df(self, mock_get, fetcher):
        mock_get.side_effect = Exception("Connection refused")
        df = fetcher.fetch("BTCUSDT", "1d")
        assert df.empty

    @patch("requests.Session.get")
    def test_http_error_returns_empty_df(self, mock_get, fetcher):
        resp = MagicMock()
        resp.raise_for_status.side_effect = Exception("400 Bad Request")
        mock_get.return_value = resp
        df = fetcher.fetch("INVALIDPAIR", "1d")
        assert df.empty

    def test_invalid_timeframe_returns_empty_df(self, fetcher):
        df = fetcher.fetch("BTCUSDT", "5m")
        assert df.empty


# ---------------------------------------------------------------------------
# Test: validate_symbol
# ---------------------------------------------------------------------------

class TestValidateSymbol:

    @patch("requests.Session.get")
    def test_valid_symbol_returns_true(self, mock_get, fetcher):
        mock_get.return_value = mock_response(make_klines(1))
        assert fetcher.validate_symbol("BTCUSDT") is True

    @patch("requests.Session.get")
    def test_invalid_symbol_returns_false(self, mock_get, fetcher):
        mock_get.return_value = mock_response([], status_code=400)
        assert fetcher.validate_symbol("NOTAPAIR") is False

    @patch("requests.Session.get")
    def test_exception_returns_false(self, mock_get, fetcher):
        mock_get.side_effect = Exception("Timeout")
        assert fetcher.validate_symbol("BTCUSDT") is False


# ---------------------------------------------------------------------------
# Test: symbol list
# ---------------------------------------------------------------------------

class TestSymbolList:

    def test_crypto_symbols_not_empty(self):
        from app.services.data.binance_fetcher import CRYPTO_SYMBOLS
        assert len(CRYPTO_SYMBOLS) >= 10

    def test_all_symbols_end_with_usdt(self):
        from app.services.data.binance_fetcher import CRYPTO_SYMBOLS
        for sym in CRYPTO_SYMBOLS:
            assert sym.endswith("USDT"), f"Symbol {sym} should end with USDT"

    def test_all_symbols_uppercase(self):
        from app.services.data.binance_fetcher import CRYPTO_SYMBOLS
        for sym in CRYPTO_SYMBOLS:
            assert sym == sym.upper(), f"Symbol {sym} not uppercase"


# ---------------------------------------------------------------------------
# Test: interface compliance — same schema as yfinance
# ---------------------------------------------------------------------------

class TestInterfaceCompliance:

    @patch("requests.Session.get")
    def test_same_columns_as_yfinance(self, mock_get, fetcher):
        """
        Binance and yfinance must return the SAME columns.
        This ensures the pipeline treats both identically.
        """
        mock_get.return_value = mock_response(make_klines(5))
        df = fetcher.fetch("BTCUSDT", "1d")

        assert set(df.columns) >= REQUIRED_COLUMNS

    @patch("requests.Session.get")
    def test_validate_output_passes(self, mock_get, fetcher):
        """_validate_output() from BaseDataFetcher must return True."""
        mock_get.return_value = mock_response(make_klines(5))
        df = fetcher.fetch("BTCUSDT", "1d")
        assert fetcher._validate_output(df) is True
