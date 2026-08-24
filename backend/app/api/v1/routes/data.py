"""
TradeFlow AI — Data API Routes
Day 19: Real MongoDB queries wired into FastAPI routes.

Endpoints built today:
  GET  /api/v1/data/indicators/{symbol}        → latest indicator snapshot
  GET  /api/v1/data/indicators/{symbol}/history → indicator history
  GET  /api/v1/data/patterns/{symbol}           → recent chart patterns

CSV upload and price bars endpoints come on Day 28
when we have the yfinance fetcher built.
"""
from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, HTTPException, Query

from app.services.mongo_service import indicators, chart_patterns

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get(
    "/indicators/{symbol}",
    summary="Get latest indicator snapshot for a symbol",
    response_description="Most recent EMA, RSI, MACD, Bollinger, ATR, OBV values",
)
async def get_latest_indicators(
    symbol: str,
    timeframe: str = Query(
        default="1d",
        regex="^(1d|1h|15m)$",
        description="Bar timeframe: 1d, 1h, or 15m",
    ),
) -> Dict[str, Any]:
    """
    Returns the most recent indicator snapshot for a symbol.

    Used by:
    - Claude signal generation (needs current indicator state)
    - Signal detail page (show EMA, RSI values alongside the signal)
    - Dashboard signal cards (indicator summary)

    Returns 404 if no indicator data exists yet
    (symbol has not been processed by the pipeline).
    """
    doc = await indicators.get_latest(
        symbol=symbol,
        timeframe=timeframe,
    )

    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"No indicator data found for {symbol.upper()} ({timeframe}). "
                   f"Run the pipeline first.",
        )

    return doc


@router.get(
    "/indicators/{symbol}/history",
    summary="Get indicator history for a symbol",
    response_description="List of indicator snapshots ordered newest first",
)
async def get_indicator_history(
    symbol: str,
    timeframe: str = Query(default="1d", regex="^(1d|1h|15m)$"),
    limit: int = Query(default=100, ge=1, le=500),
) -> List[Dict[str, Any]]:
    """
    Returns the last N indicator snapshots for a symbol.

    Used by:
    - Backtest engine (needs historical indicator values for strategy signals)
    - Chart overlays (EMA lines on the chart)

    Sorted newest first — index 0 is the most recent bar.
    """
    docs = await indicators.get_history(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )

    if not docs:
        raise HTTPException(
            status_code=404,
            detail=f"No indicator history found for {symbol.upper()} ({timeframe}).",
        )

    return docs


@router.get(
    "/patterns/{symbol}",
    summary="Get recent chart patterns for a symbol",
    response_description="Candlestick patterns detected in the last N days",
)
async def get_chart_patterns(
    symbol: str,
    timeframe: str = Query(default="1d", regex="^(1d|1h|15m)$"),
    days: int = Query(default=5, ge=1, le=30, description="Look back N days"),
    bullish_only: bool = Query(default=False),
    bearish_only: bool = Query(default=False),
) -> List[Dict[str, Any]]:
    """
    Returns candlestick patterns detected recently for a symbol.

    Used by:
    - Claude signal prompt (tell AI which patterns appeared)
    - Signal card pattern_tags badges
    - Backtest pattern strategies

    signal_value: 100 = bullish, -100 = bearish
    """
    if bullish_only and bearish_only:
        raise HTTPException(
            status_code=400,
            detail="Cannot set both bullish_only and bearish_only to true.",
        )

    docs = await chart_patterns.get_recent_patterns(
        symbol=symbol,
        timeframe=timeframe,
        days=days,
        bullish_only=bullish_only,
        bearish_only=bearish_only,
    )

    # Empty list is valid — symbol exists but no patterns detected recently
    return docs


@router.get("/status")
async def data_status():
    """Confirms data router is registered."""
    return {
        "router": "data",
        "endpoints": [
            "GET /indicators/{symbol}",
            "GET /indicators/{symbol}/history",
            "GET /patterns/{symbol}",
            "GET /bars/{symbol}         (coming Day 28)",
            "POST /upload-csv           (coming Day 28)",
            "GET /instruments/search    (coming Day 28)",
        ],
    }
