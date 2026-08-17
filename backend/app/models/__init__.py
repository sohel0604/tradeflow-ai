# Import ALL models here so Alembic can find them
# when auto-generating migrations.
# Every new model MUST be added to this file.

from app.models.price        import PriceBar, FetchLog
from app.models.user         import User, AuthToken, ApiKey, BrokerCredential
from app.models.signal       import Signal
from app.models.backtest     import BacktestResult, UserStrategyConfig
from app.models.watchlist    import UserWatchlist
from app.models.billing      import Subscription
from app.models.paper_trading import (
    PaperPortfolio,
    PaperPosition,
    PaperTrade,
)

__all__ = [
    # Phase 1 — Data pipeline
    "PriceBar",
    "FetchLog",
    # Auth
    "User",
    "AuthToken",
    "ApiKey",
    "BrokerCredential",
    # Phase 3 — Signals
    "Signal",
    # Phase 2 — Backtest
    "BacktestResult",
    "UserStrategyConfig",
    # Phase 4 — API
    "UserWatchlist",
    "Subscription",
    # Phase 7 — Paper trading
    "PaperPortfolio",
    "PaperPosition",
    "PaperTrade",
]
