"""
TradeFlow AI — Price Data Models
Day 10: PriceBar and FetchLog

PriceBar → stores every OHLCV candle for every instrument
FetchLog → records every data fetch attempt (success or failure)

These are the foundation of the entire platform.
Everything else (indicators, patterns, signals) is built on top of these.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PriceBar(Base):
    """
    One OHLCV candle for one instrument at one timeframe.

    Example row:
        symbol     = "RELIANCE.NS"
        timeframe  = "1d"
        timestamp  = 2024-01-15 00:00:00+00 (UTC)
        open       = 2567.50
        high       = 2589.00
        low        = 2551.25
        close      = 2578.90
        volume     = 4521000.0
        asset_type = "equity"

    The UNIQUE constraint on (symbol, timeframe, timestamp) means:
    - You can insert the same symbol many times (different dates) ✅
    - You can insert the same date many times (different symbols) ✅
    - You CANNOT insert the same symbol+timeframe+date twice ❌
    This makes our data pipeline idempotent — safe to re-run.
    """
    __tablename__ = "price_bars"

    # ---------------------------------------------------------------------------
    # Primary Key
    # We use UUID instead of auto-increment integer because:
    # - UUID is globally unique (safe across multiple services)
    # - Auto-increment leaks info (attacker knows how many rows we have)
    # - UUID is the standard for distributed systems
    # ---------------------------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ---------------------------------------------------------------------------
    # Core OHLCV columns
    # ---------------------------------------------------------------------------
    symbol = Column(
        String(50),
        nullable=False,
        comment="Ticker symbol e.g. RELIANCE.NS, BTCUSDT, EURUSD=X",
    )
    timeframe = Column(
        String(10),
        nullable=False,
        comment="Bar timeframe: 1d, 1h, or 15m",
    )
    timestamp = Column(
        DateTime(timezone=True),    # ALWAYS timezone-aware — stores as UTC
        nullable=False,
        comment="Bar open time in UTC",
    )
    open = Column(Float, nullable=False, comment="Opening price")
    high = Column(Float, nullable=False, comment="Highest price in the bar")
    low = Column(Float, nullable=False, comment="Lowest price in the bar")
    close = Column(Float, nullable=False, comment="Closing price")
    volume = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Trading volume (0 for forex where volume is not meaningful)",
    )

    # ---------------------------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------------------------
    asset_type = Column(
        String(20),
        nullable=False,
        comment="One of: equity, crypto, forex, commodity, custom",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="When this row was inserted",
    )

    # ---------------------------------------------------------------------------
    # Constraints and Indexes
    # Defined at the table level inside __table_args__
    # ---------------------------------------------------------------------------
    __table_args__ = (
        # UNIQUE CONSTRAINT
        # Prevents duplicate bars — this is the idempotency guarantee
        # ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING uses this
        UniqueConstraint(
            "symbol",
            "timeframe",
            "timestamp",
            name="uq_price_bars_symbol_tf_ts",
        ),

        # INDEX 1: symbol + timeframe
        # Most queries filter by both — this makes them fast
        # e.g. "get all daily bars for RELIANCE.NS"
        Index("ix_price_bars_symbol_timeframe", "symbol", "timeframe"),

        # INDEX 2: timestamp
        # Date range queries — "get all bars after 2024-01-01"
        Index("ix_price_bars_timestamp", "timestamp"),

        # INDEX 3: asset_type
        # Filter by asset class — "show only crypto signals"
        Index("ix_price_bars_asset_type", "asset_type"),
    )

    def __repr__(self) -> str:
        """Readable representation for debugging."""
        return (
            f"<PriceBar {self.symbol} {self.timeframe} "
            f"{self.timestamp} C={self.close}>"
        )


class FetchLog(Base):
    """
    Records every data fetch attempt — whether it succeeded or failed.

    Why log failures?
    - The ops alert system (Day 36) queries this to detect
      symbols that have failed for 2+ consecutive days
    - You can debug data gaps by looking at fetch history
    - It proves to auditors that you attempted to fetch data

    Every pipeline run creates rows here regardless of outcome.
    Never delete these rows — they are your audit trail.
    """
    __tablename__ = "fetch_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)

    # "SUCCESS", "FAILED", or "PARTIAL" (some rows saved but not all)
    status = Column(String(20), nullable=False)

    # How many rows were actually inserted into price_bars
    rows_saved = Column(Integer, default=0, nullable=False)

    # If status=FAILED, what was the error? None if SUCCESS.
    error_msg = Column(Text, nullable=True)

    # When did this fetch happen?
    fetched_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Where did the data come from?
    # "yfinance", "binance", "csv", "dhan"
    source = Column(
        String(20),
        nullable=False,
        default="yfinance",
    )

    __table_args__ = (
        # Find all recent failures for a symbol quickly
        Index("ix_fetch_logs_symbol_status", "symbol", "status"),
        # Query by date — "show me all fetches from today"
        Index("ix_fetch_logs_fetched_at", "fetched_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<FetchLog {self.symbol} {self.timeframe} "
            f"{self.status} rows={self.rows_saved}>"
        )
