"""
TradeFlow AI — Backtest Schemas
Day 18: Request/response models for backtest results.
"""
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BacktestResultResponse(BaseModel):
    """Full backtest result — shown in the Backtest Explorer page."""
    id: UUID
    symbol: str
    strategy: str
    run_date: datetime
    win_rate: float | None = Field(None, ge=0.0, le=1.0)
    avg_rr: float | None
    sharpe_ratio: float | None
    max_drawdown: float | None
    profit_factor: float | None
    total_trades: int
    passed: bool
    parameters: Dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BacktestTradeLog(BaseModel):
    """
    One trade from the full backtest trade-by-trade log.
    Stored in MongoDB — not a SQLAlchemy model.
    """
    entry_date: datetime
    exit_date: datetime
    direction: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float


class BacktestFilterParams(BaseModel):
    """Query params for GET /api/v1/backtest/results."""
    symbol: str | None = None
    strategy: str | None = None
    passed_only: bool = False
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class OnDemandBacktestRequest(BaseModel):
    """
    Body for POST /api/v1/backtest/run (Business tier only).
    Triggers an on-demand backtest for a specific symbol + strategy.
    """
    symbol: str = Field(
        min_length=1,
        max_length=50,
        description="Symbol to backtest e.g. RELIANCE.NS",
    )
    strategy: str = Field(
        description="Strategy name: ema_crossover | rsi_reversal | macd | bollinger",
    )
    parameters: Dict[str, Any] | None = Field(
        None,
        description="Optional parameter overrides. Uses user config or defaults if omitted.",
    )

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        valid = {"ema_crossover", "rsi_reversal", "macd", "bollinger"}
        if v not in valid:
            raise ValueError(f"strategy must be one of: {', '.join(sorted(valid))}")
        return v


class OnDemandBacktestResponse(BaseModel):
    """Response after triggering an on-demand backtest."""
    task_id: str
    status: str = "PENDING"
    message: str = "Backtest queued. Poll /api/v1/backtest/status/{task_id} for result."


class BacktestStatusResponse(BaseModel):
    """Response from polling GET /api/v1/backtest/status/{task_id}."""
    task_id: str
    status: str   # PENDING | SUCCESS | FAILURE
    result: BacktestResultResponse | None = None
    error: str | None = None
