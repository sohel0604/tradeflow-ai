"""
TradeFlow AI — Signal Model
Day 12: AI-generated trading signals

One signal = one Claude AI decision for one symbol on one day.
Contains everything needed to act on the signal:
entry price, stop-loss, take-profits, reasoning, chart image URL.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Float, Index,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.core.database import Base


class Signal(Base):
    """
    AI-generated BUY / SELL / HOLD signal for one instrument.

    Lifecycle of a signal:
    1. Backtest passes filter (win_rate >= 50%, avg_rr >= 1.5)
    2. Claude API generates: direction, entry, SL, TP1, TP2, reasoning
    3. mplfinance generates an annotated chart PNG
    4. Signal stored here with outcome = "OPEN"
    5. Daily outcome checker updates to WIN / LOSS / EXPIRED

    outcome values:
    - OPEN    → signal is active, waiting for SL or TP to be hit
    - WIN     → price reached take_profit_1
    - LOSS    → price touched stop_loss
    - EXPIRED → 20 trading days passed without hitting either level
    """
    __tablename__ = "signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which instrument and which strategy generated this signal
    symbol   = Column(String(50), nullable=False)
    strategy = Column(
        String(100),
        nullable=False,
        comment="e.g. ema_crossover, rsi_reversal, pattern_hammer",
    )

    # The date this signal was generated (one signal per symbol+strategy+day)
    signal_date = Column(DateTime(timezone=True), nullable=False)

    # Claude's decision
    direction = Column(
        String(10),
        nullable=False,
        comment="BUY | SELL | HOLD",
    )

    # Price levels — all from Claude's analysis
    entry_price  = Column(Float, nullable=True)
    stop_loss    = Column(Float, nullable=True)
    take_profit_1 = Column(Float, nullable=True)
    take_profit_2 = Column(Float, nullable=True)

    # Claude's confidence in this signal (0.0 to 1.0)
    confidence = Column(Float, nullable=True)

    # 2-4 sentences from Claude explaining WHY this signal was generated
    reasoning = Column(Text, nullable=True)

    # Backtest stats that informed this signal
    win_rate = Column(Float, nullable=True)
    avg_rr   = Column(Float, nullable=True)

    # URL of the annotated mplfinance chart PNG (S3 in prod, /charts/ in dev)
    chart_image_url = Column(Text, nullable=True)

    # Current outcome — updated daily by the outcome checker task
    outcome = Column(
        String(10),
        default="OPEN",
        nullable=False,
        comment="OPEN | WIN | LOSS | EXPIRED",
    )

    # Which candlestick patterns contributed to this signal
    # e.g. ["hammer", "ema_crossover", "rsi_oversold"]
    pattern_tags = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=datetime.utcnow,
        nullable=True,
    )

    __table_args__ = (
        # One signal per symbol+strategy per day — no duplicates
        UniqueConstraint(
            "symbol", "strategy", "signal_date",
            name="uq_signal_symbol_strategy_date",
        ),
        Index("ix_signals_symbol_date", "symbol", "signal_date"),
        Index("ix_signals_direction",   "direction"),
        Index("ix_signals_outcome",     "outcome"),
    )

    def __repr__(self) -> str:
        return (
            f"<Signal {self.symbol} {self.direction} "
            f"@ {self.signal_date} outcome={self.outcome}>"
        )
