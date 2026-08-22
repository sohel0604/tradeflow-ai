# Re-export all schemas for clean imports
# Usage: from app.schemas import PaginatedResponse, SignalResponse

from app.schemas.common import (
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
    HealthResponse,
    DatabaseHealthResponse,
)
from app.schemas.price import (
    PriceBarResponse,
    PriceBarCreate,
    ChartBarResponse,
    FetchLogResponse,
    CSVUploadResponse,
    InstrumentSearchResult,
)
from app.schemas.signal import (
    SignalResponse,
    SignalListItem,
    SignalFilterParams,
)
from app.schemas.backtest import (
    BacktestResultResponse,
    BacktestTradeLog,
    BacktestFilterParams,
    OnDemandBacktestRequest,
    OnDemandBacktestResponse,
    BacktestStatusResponse,
)

__all__ = [
    # Common
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthResponse",
    "DatabaseHealthResponse",
    # Price
    "PriceBarResponse",
    "PriceBarCreate",
    "ChartBarResponse",
    "FetchLogResponse",
    "CSVUploadResponse",
    "InstrumentSearchResult",
    # Signals
    "SignalResponse",
    "SignalListItem",
    "SignalFilterParams",
    # Backtest
    "BacktestResultResponse",
    "BacktestTradeLog",
    "BacktestFilterParams",
    "OnDemandBacktestRequest",
    "OnDemandBacktestResponse",
    "BacktestStatusResponse",
]
