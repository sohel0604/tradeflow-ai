"""
TradeFlow AI — MongoDB Service Layer
Day 19: Async queries for indicators and chart_patterns collections.

Why a service layer between routes and MongoDB?
- Routes stay thin — just HTTP handling
- Business logic (queries, transforms) lives here
- Easy to test — mock this class, not the DB
- If we switch DB, only this file changes

Collections we query today:
  indicators     → EMA, RSI, MACD, Bollinger per symbol+timeframe+date
  chart_patterns → detected candlestick patterns per symbol
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import (
    get_indicators_collection,
    get_chart_patterns_collection,
)

logger = structlog.get_logger(__name__)


# =============================================================================
# Indicator Service
# =============================================================================

class IndicatorService:
    """
    Reads indicator data from the MongoDB `indicators` collection.

    Document structure in MongoDB:
    {
        "symbol":    "RELIANCE.NS",
        "timeframe": "1d",
        "timestamp": ISODate("2024-01-15T00:00:00Z"),
        "close":     2578.90,
        "indicators": {
            "ema_9":          2567.3,
            "ema_21":         2554.1,
            "ema_50":         2521.8,
            "ema_200":        2410.2,
            "rsi_14":         62.4,
            "macd_line":      1.23,
            "macd_signal":    0.98,
            "macd_histogram": 0.25,
            "bb_upper":       2601.5,
            "bb_middle":      2556.2,
            "bb_lower":       2510.9,
            "bb_bandwidth":   3.55,
            "bb_percent":     0.61,
            "atr_14":         28.4,
            "obv":            45231000.0
        }
    }
    """

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return get_indicators_collection()

    async def get_latest(
        self,
        symbol: str,
        timeframe: str = "1d",
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent indicator snapshot for a symbol.
        Used when generating AI signals — Claude needs the latest indicators.

        Returns None if no indicator data exists (symbol not yet processed).
        """
        doc = await self.collection.find_one(
            {"symbol": symbol.upper(), "timeframe": timeframe},
            # Sort by timestamp descending — most recent first
            sort=[("timestamp", -1)],
            # Exclude MongoDB's internal _id from response
            projection={"_id": 0},
        )

        if doc:
            logger.debug(
                "indicators_fetched",
                symbol=symbol,
                timeframe=timeframe,
                timestamp=str(doc.get("timestamp")),
            )

        return doc

    async def get_history(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get the last N indicator snapshots for a symbol.
        Used by the backtest engine to access historical indicator values.

        MongoDB .find() returns a cursor — we call .to_list() to
        materialise it into a Python list.
        """
        cursor = self.collection.find(
            {"symbol": symbol.upper(), "timeframe": timeframe},
            sort=[("timestamp", -1)],
            limit=limit,
            projection={"_id": 0},
        )
        docs = await cursor.to_list(length=limit)

        logger.debug(
            "indicator_history_fetched",
            symbol=symbol,
            timeframe=timeframe,
            count=len(docs),
        )

        return docs

    async def get_indicator_value(
        self,
        symbol: str,
        indicator: str,
        timeframe: str = "1d",
    ) -> Optional[float]:
        """
        Get a single indicator value for a symbol.

        Example: get_indicator_value("BTCUSDT", "rsi_14")
        → 62.4

        Uses MongoDB dot notation to query nested fields:
        "indicators.rsi_14" → reads the rsi_14 field inside the indicators object.
        """
        doc = await self.collection.find_one(
            {"symbol": symbol.upper(), "timeframe": timeframe},
            sort=[("timestamp", -1)],
            # Only fetch the specific indicator we need (faster)
            projection={"_id": 0, f"indicators.{indicator}": 1},
        )

        if doc and "indicators" in doc:
            return doc["indicators"].get(indicator)
        return None

    async def upsert(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        indicators: Dict[str, Any],
        close: float,
    ) -> None:
        """
        Insert or update an indicator document.
        Called by the Celery indicator computation task (Day 41).

        Uses update_one with upsert=True:
        - If a document with matching symbol+timeframe+timestamp exists → update it
        - If not → insert a new document
        This makes the pipeline idempotent (safe to re-run).
        """
        # Ensure timestamp is UTC timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        await self.collection.update_one(
            # Match condition — unique key for a snapshot
            {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "timestamp": timestamp,
            },
            # $set — update these fields (or create them)
            {
                "$set": {
                    "symbol": symbol.upper(),
                    "timeframe": timeframe,
                    "timestamp": timestamp,
                    "close": close,
                    "indicators": indicators,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    async def ensure_indexes(self) -> None:
        """
        Create MongoDB indexes for fast queries.
        Called once at app startup.

        Compound index on (symbol, timeframe, timestamp):
        - Covers the most common query pattern
        - unique=True prevents duplicate snapshots
        """
        await self.collection.create_index(
            [
                ("symbol", 1),
                ("timeframe", 1),
                ("timestamp", -1),
            ],
            unique=True,
            name="ix_indicators_symbol_tf_ts",
        )
        logger.info("indicators_indexes_created")


# =============================================================================
# Chart Pattern Service
# =============================================================================

class ChartPatternService:
    """
    Reads detected candlestick patterns from MongoDB `chart_patterns`.

    Document structure:
    {
        "symbol":       "RELIANCE.NS",
        "timeframe":    "1d",
        "timestamp":    ISODate("2024-01-15T00:00:00Z"),
        "pattern_name": "hammer",
        "signal_value": 100,       // 100=bullish, -100=bearish
        "confirmed":    true
    }
    """

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return get_chart_patterns_collection()

    async def get_recent_patterns(
        self,
        symbol: str,
        timeframe: str = "1d",
        days: int = 5,
        bullish_only: bool = False,
        bearish_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get patterns detected in the last N days for a symbol.
        Used when building the Claude signal prompt —
        we tell Claude which patterns appeared recently.

        signal_value filter:
        - bullish_only → signal_value > 0   (bullish patterns)
        - bearish_only → signal_value < 0   (bearish patterns)
        - neither      → all patterns
        """
        from datetime import timedelta

        since = datetime.now(timezone.utc) - timedelta(days=days)

        query: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "timestamp": {"$gte": since},
        }

        if bullish_only:
            query["signal_value"] = {"$gt": 0}
        elif bearish_only:
            query["signal_value"] = {"$lt": 0}

        cursor = self.collection.find(
            query,
            sort=[("timestamp", -1)],
            projection={"_id": 0},
        )
        docs = await cursor.to_list(length=50)

        logger.debug(
            "patterns_fetched",
            symbol=symbol,
            timeframe=timeframe,
            count=len(docs),
        )

        return docs

    async def get_pattern_names(self, symbol: str, timeframe: str = "1d") -> List[str]:
        """
        Get a list of distinct pattern names detected recently.
        Returns e.g. ["hammer", "ema_crossover", "rsi_oversold"]
        Used to populate the pattern_tags field on signals.
        """
        docs = await self.get_recent_patterns(symbol, timeframe, days=3)
        return list({doc["pattern_name"] for doc in docs})

    async def upsert(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        pattern_name: str,
        signal_value: int,
        confirmed: bool = True,
    ) -> None:
        """
        Store a detected pattern.
        Called by the TA-Lib pattern scanner Celery task (Day 55).
        """
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        await self.collection.update_one(
            {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "timestamp": timestamp,
                "pattern_name": pattern_name,
            },
            {
                "$set": {
                    "symbol": symbol.upper(),
                    "timeframe": timeframe,
                    "timestamp": timestamp,
                    "pattern_name": pattern_name,
                    "signal_value": signal_value,
                    "confirmed": confirmed,
                }
            },
            upsert=True,
        )

    async def ensure_indexes(self) -> None:
        """Create indexes for fast pattern queries."""
        await self.collection.create_index(
            [("symbol", 1), ("timeframe", 1), ("timestamp", -1)],
            name="ix_patterns_symbol_tf_ts",
        )
        await self.collection.create_index(
            [("pattern_name", 1)],
            name="ix_patterns_name",
        )
        logger.info("chart_patterns_indexes_created")


# =============================================================================
# Module-level singletons
# Import these in routes and tasks: from app.services.mongo_service import indicators
# =============================================================================
indicators = IndicatorService()
chart_patterns = ChartPatternService()
