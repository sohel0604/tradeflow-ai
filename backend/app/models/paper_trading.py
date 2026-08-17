"""
TradeFlow AI — Paper Trading Models
Day 12: PaperPortfolio, PaperPosition, PaperTrade

Paper trading = practice trading with virtual money.
No real money is involved — users learn to trade risk-free.

How it works:
1. User sees a BUY signal for RELIANCE.NS
2. They click "Take This Trade (Paper)"
3. A PaperPosition is opened at the signal's entry price
4. Each day the pipeline checks if SL or TP was hit
5. When hit, the position is closed and a PaperTrade is recorded
6. The portfolio balance updates with the P&L

Three tables:
- PaperPortfolio → the overall account (balance, stats)
- PaperPosition  → one open trade (entry price, SL, TP levels)
- PaperTrade     → one closed trade (entry, exit, P&L, reason)
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float,
    ForeignKey, Index, String,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PaperPortfolio(Base):
    """
    The user's virtual trading account.

    starting_balance → fixed at creation (default INR 1,00,000)
    current_balance  → updates after every trade closes

    Formula:
        current_balance = starting_balance + sum(all realised P&L)

    Users can reset their portfolio — the old one is archived
    (is_active=False) and a new one is created.
    """
    __tablename__ = "paper_portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    starting_balance = Column(
        Float,
        default=100000.0,
        nullable=False,
        comment="INR 1,00,000 default starting capital",
    )
    current_balance = Column(
        Float,
        default=100000.0,
        nullable=False,
        comment="Starting balance + all realised P&L",
    )

    # False = this portfolio was reset — kept for history
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<PaperPortfolio user={self.user_id} "
            f"balance={self.current_balance} active={self.is_active}>"
        )


class PaperPosition(Base):
    """
    One open paper trade.

    Stays OPEN until:
    - Stop-loss is hit → status = CLOSED, exit_reason = SL_HIT
    - Take-profit 1 is hit → status = CLOSED, exit_reason = TP1_HIT
    - Take-profit 2 is hit → status = CLOSED, exit_reason = TP2_HIT
    - User manually closes → status = CLOSED, exit_reason = MANUAL

    direction:
    - LONG  → bought, profit if price goes UP
    - SHORT → sold, profit if price goes DOWN
    """
    __tablename__ = "paper_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    portfolio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("paper_portfolios.id"),
        nullable=False,
    )

    # The signal that triggered this trade (nullable — user can open manually)
    signal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("signals.id"),
        nullable=True,
    )

    symbol    = Column(String(50), nullable=False)
    direction = Column(String(10), nullable=False, comment="LONG | SHORT")

    # Entry price = signal's entry_price (NOT live market price)
    # This prevents cheating by entering at a better price
    entry_price = Column(Float, nullable=False)

    # How many shares/units
    quantity = Column(Float, nullable=False)

    # Price levels copied from the signal
    stop_loss    = Column(Float, nullable=True)
    take_profit_1 = Column(Float, nullable=True)
    take_profit_2 = Column(Float, nullable=True)

    opened_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    status    = Column(
        String(10),
        default="OPEN",
        nullable=False,
        comment="OPEN | CLOSED",
    )

    __table_args__ = (
        Index("ix_paper_positions_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<PaperPosition {self.symbol} {self.direction} "
            f"qty={self.quantity} status={self.status}>"
        )


class PaperTrade(Base):
    """
    One completed (closed) paper trade.

    Created when a PaperPosition is closed for any reason.
    This is the permanent record used for analytics:
    - Win rate calculation
    - P&L tracking
    - Strategy performance comparison

    P&L formula:
    - LONG:  pnl = (exit_price - entry_price) * quantity
    - SHORT: pnl = (entry_price - exit_price) * quantity
    """
    __tablename__ = "paper_trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    position_id = Column(
        UUID(as_uuid=True),
        ForeignKey("paper_positions.id"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    symbol    = Column(String(50), nullable=False)
    direction = Column(String(10), nullable=False)

    entry_price = Column(Float, nullable=False)
    exit_price  = Column(Float, nullable=False)
    quantity    = Column(Float, nullable=False)

    # Positive = profit, Negative = loss (in INR)
    pnl = Column(Float, nullable=False)

    opened_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    exit_reason = Column(
        String(20),
        nullable=False,
        comment="SL_HIT | TP1_HIT | TP2_HIT | MANUAL | EXPIRED",
    )

    def __repr__(self) -> str:
        return (
            f"<PaperTrade {self.symbol} pnl={self.pnl} "
            f"reason={self.exit_reason}>"
        )
