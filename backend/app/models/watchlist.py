"""
TradeFlow AI — Watchlist Model
Day 12: UserWatchlist

Users choose which instruments to track.
Free tier: max 3 symbols.
Pro/Business tier: unlimited.

When a symbol is added:
- Its signals are included in the user's daily digest
- Historical data is backfilled if not already in price_bars
- WebSocket pushes signals for this symbol to the user

When a symbol is removed:
- Future signals for it stop being delivered to this user
- Historical data stays in price_bars (shared across users)
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, ForeignKey,
    Index, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserWatchlist(Base):
    __tablename__ = "user_watchlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Ticker symbol exactly as used in fetchers
    # e.g. "RELIANCE.NS", "BTCUSDT", "EURUSD=X"
    symbol = Column(String(50), nullable=False)

    # Helps filter signals by asset class in the dashboard
    asset_type = Column(
        String(20),
        nullable=False,
        comment="equity | crypto | forex | commodity | custom",
    )

    added_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        # A user can't add the same symbol twice
        UniqueConstraint(
            "user_id", "symbol",
            name="uq_watchlist_user_symbol",
        ),
        Index("ix_watchlist_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UserWatchlist {self.symbol} user={self.user_id}>"
