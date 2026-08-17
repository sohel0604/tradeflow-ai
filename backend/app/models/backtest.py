"""
TradeFlow AI — Backtest Models
Day 12: BacktestResult and UserStrategyConfig

BacktestResult = outcome of running a strategy against historical data
UserStrategyConfig = per-user parameter overrides (Pro/Business tier)
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float,
    Index, Integer, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.core.database import Base


class BacktestResult(Base):
    """
    Result of backtesting one strategy on one symbol on one run date.

    The statistical filter (Day 51):
    - passed = True  when win_rate >= 50% AND avg_rr >= 1.5
    - passed = False otherwise

    Only passed=True results feed into AI signal generation.
    This prevents Claude from generating signals on strategies
    that historically don't work.

    The 6 metrics stored here:
    1. win_rate     → % of trades that were profitable
    2. avg_rr       → average risk-reward ratio (profit/loss per trade)
    3. sharpe_ratio → risk-adjusted return (higher = better)
    4. max_drawdown → biggest peak-to-trough loss (lower = better)
    5. profit_factor → gross profit / gross loss (> 1 = profitable)
    6. total_trades → number of trades in the backtest period
    """
    __tablename__ = "backtest_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    symbol   = Column(String(50),  nullable=False)
    strategy = Column(String(100), nullable=False)

    # When this backtest was run (daily — one row per run)
    run_date = Column(DateTime(timezone=True), nullable=False)

    # The 6 metrics
    win_rate     = Column(Float,   nullable=True)
    avg_rr       = Column(Float,   nullable=True)
    sharpe_ratio = Column(Float,   nullable=True)
    max_drawdown = Column(Float,   nullable=True)
    profit_factor = Column(Float,  nullable=True)
    total_trades  = Column(Integer, default=0, nullable=False)

    # Did this strategy pass the quality filter?
    # True = win_rate >= 50% AND avg_rr >= 1.5
    passed = Column(Boolean, default=False, nullable=False)

    # Strategy parameters used for this run
    # e.g. {"fast_period": 9, "slow_period": 21} for EMA crossover
    parameters = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        # Re-running the daily pipeline upserts instead of inserting duplicates
        UniqueConstraint(
            "symbol", "strategy", "run_date",
            name="uq_backtest_symbol_strategy_date",
        ),
        Index("ix_backtest_symbol_strategy", "symbol", "strategy"),
        Index("ix_backtest_passed",          "passed"),
        Index("ix_backtest_run_date",        "run_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<BacktestResult {self.symbol} {self.strategy} "
            f"win={self.win_rate} passed={self.passed}>"
        )


class UserStrategyConfig(Base):
    """
    Per-user strategy parameter overrides (Pro/Business tier).

    Example: by default, RSI strategy uses oversold=30, overbought=70.
    A Pro user can override to oversold=25, overbought=75.
    Their backtest and signals use these custom values.

    Default fallback:
    If no row exists for a user+strategy, the pipeline
    uses the hardcoded defaults in the strategy class.
    """
    __tablename__ = "user_strategy_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    strategy_name = Column(String(100), nullable=False)

    # JSON object of parameter overrides
    # e.g. {"oversold": 25, "overbought": 75}
    parameters_json = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    __table_args__ = (
        # One config per user per strategy
        UniqueConstraint(
            "user_id", "strategy_name",
            name="uq_user_strategy_config",
        ),
    )

    def __repr__(self) -> str:
        return f"<UserStrategyConfig {self.strategy_name} user={self.user_id}>"
