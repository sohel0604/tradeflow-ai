"""
TradeFlow AI — Application Configuration
Day 9: Reads all environment variables from .env using pydantic-settings.

Why pydantic-settings?
- Reads .env file automatically
- Type-checks every variable (catches mistakes early)
- Gives you autocomplete in your IDE
- @lru_cache means Settings() is only created ONCE, not on every request
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration for the application.
    Values are loaded from environment variables / .env file.
    Types are validated automatically by pydantic.
    """

    model_config = SettingsConfigDict(
        # Which file to read
        env_file=".env",
        env_file_encoding="utf-8",
        # Don't crash if there are extra variables in .env we don't use
        extra="ignore",
        # Variable names are case-insensitive
        case_sensitive=False,
    )

    # -------------------------------------------------------------------------
    # App
    # -------------------------------------------------------------------------
    app_env: str = "development"
    app_secret_key: str = "changeme"
    debug: bool = True
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Split comma-separated origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",")]

    # -------------------------------------------------------------------------
    # PostgreSQL
    # -------------------------------------------------------------------------
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "tradeflow"
    postgres_user: str = "tradeflow"
    postgres_password: str = "tradeflow123"

    # Full async connection URL — used by FastAPI + SQLAlchemy
    database_url: str = (
        "postgresql+asyncpg://tradeflow:tradeflow123@postgres:5432/tradeflow"
    )

    # Sync URL — used by Alembic migrations and Celery tasks
    database_url_sync: str = (
        "postgresql://tradeflow:tradeflow123@postgres:5432/tradeflow"
    )

    # -------------------------------------------------------------------------
    # MongoDB
    # -------------------------------------------------------------------------
    mongo_uri: str = (
        "mongodb://tradeflow:tradeflow123@mongodb:27017/tradeflow?authSource=admin"
    )
    mongo_db: str = "tradeflow"

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    redis_url: str = "redis://:tradeflow123@redis:6379/0"

    # -------------------------------------------------------------------------
    # Celery (used from Day 31)
    # -------------------------------------------------------------------------
    celery_broker_url: str = "redis://:tradeflow123@redis:6379/0"
    celery_result_backend: str = "redis://:tradeflow123@redis:6379/1"
    celery_worker_concurrency: int = 4
    celery_timezone: str = "Asia/Kolkata"

    # -------------------------------------------------------------------------
    # JWT (used from Day 78)
    # -------------------------------------------------------------------------
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # -------------------------------------------------------------------------
    # AWS S3 (used from Day 70)
    # -------------------------------------------------------------------------
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-south-1"
    aws_s3_bucket: str = "tradeflow-charts"

    # -------------------------------------------------------------------------
    # External APIs (filled as we build each phase)
    # -------------------------------------------------------------------------
    anthropic_api_key: str = ""
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@tradeflow.ai"
    alert_email: str = "ops@tradeflow.ai"
    telegram_bot_token: str = ""
    slack_ops_webhook_url: str = ""
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    dhan_client_id: str = ""
    dhan_access_token: str = ""
    encryption_key: str = ""

    # -------------------------------------------------------------------------
    # Charts
    # -------------------------------------------------------------------------
    charts_dir: str = "/app/charts"
    charts_base_url: str = "http://localhost:8000/charts"


@lru_cache()
def get_settings() -> Settings:
    """
    Return cached settings instance.

    @lru_cache means this function runs ONCE and caches the result.
    Every call after the first returns the same Settings object.
    This is important because reading .env on every request would be slow.

    Usage in FastAPI:
        from app.core.config import settings
        print(settings.postgres_host)
    """
    return Settings()


# Module-level instance — import this everywhere
# from app.core.config import settings
settings = get_settings()
