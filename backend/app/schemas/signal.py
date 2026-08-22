"""
TradeFlow AI — Signal Schemas
Day 18: Request/response models for AI-generated trading signals.
"""
from datetime import datetime
from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


Direction = Literal["BUY", "SELL", "HOLD"]
Outcome = Literal["OPEN", "WIN", "LOSS", "EXPIRED"]


class SignalResponse(BaseModel):
    """
    Full signal response — everything a client needs to display a signal card.

    Contains:
    - Price levels (entry, SL, TP1, TP2)
    - AI output (direction, confidence, reasoning)
    - Backtest stats that qualified this signal
    - Chart image URL for the annotated chart PNG
    - Current outcome (WIN/LOSS/OPEN/EXPIRED)
    """
    id: UUID
    symbol: str
    strategy: str
    signal_date: datetime
    direction: Direction
    entry_price: float | None
    stop_loss: float | None
    take_profit_1: float | None
    take_profit_2: float | None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    reasoning: str | None
    win_rate: float | None
    avg_rr: float | None
    chart_image_url: str | None
    outcome: Outcome
    pattern_tags: List[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SignalListItem(BaseModel):
    """
    Compact signal for list views (dashboard card grid).
    Excludes reasoning to keep the list response small.
    """
    id: UUID
    symbol: str
    strategy: str
    signal_date: datetime
    direction: Direction
    entry_price: float | None
    stop_loss: float | None
    take_profit_1: float | None
    take_profit_2: float | None
    confidence: float | None
    win_rate: float | None
    avg_rr: float | None
    chart_image_url: str | None
    outcome: Outcome
    pattern_tags: List[str] | None

    model_config = {"from_attributes": True}


class SignalFilterParams(BaseModel):
    """
    Query parameters for GET /api/v1/signals.
    All filters are optional — omitting one means "no filter on that field".

    Usage:
        GET /api/v1/signals?direction=BUY&min_win_rate=0.55&page=1&page_size=20
    """
    symbol: str | None = None
    direction: Direction | None = None
    strategy: str | None = None
    outcome: Outcome | None = None
    min_win_rate: float | None = Field(None, ge=0.0, le=1.0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
