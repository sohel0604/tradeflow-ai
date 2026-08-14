# Import all models here so Alembic can find them when generating migrations
# Every new model we create gets added to this file

from app.models.price import PriceBar, FetchLog

__all__ = [
    "PriceBar",
    "FetchLog",
]
