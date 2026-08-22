"""
TradeFlow AI — Config Check Route
Day 17: Development-only endpoint that shows non-secret config values.

NEVER expose this in production.
It helps during development to verify .env is loaded correctly
without checking the file manually.

Returns ONLY non-sensitive values — no passwords, no API keys.
"""
from fastapi import APIRouter, HTTPException
from app.core.config import settings

router = APIRouter()


@router.get(
    "/config-check",
    tags=["dev"],
    summary="Show non-secret config (dev only)",
)
async def config_check():
    """
    Shows current config values loaded from .env.
    Only available when APP_ENV=development.
    Returns only safe, non-sensitive values.
    """
    # Block this endpoint in production
    if settings.app_env != "development":
        raise HTTPException(
            status_code=404,
            detail="Not found",  # don't hint this endpoint exists
        )

    return {
        "app_env": settings.app_env,
        "debug": settings.debug,
        "log_level": settings.log_level,
        "allowed_origins": settings.allowed_origins_list,

        # Database connectivity (no passwords)
        "postgres_host": settings.postgres_host,
        "postgres_port": settings.postgres_port,
        "postgres_db": settings.postgres_db,
        "postgres_user": settings.postgres_user,
        "postgres_password": "***hidden***",

        "mongo_db": settings.mongo_db,

        # Celery config
        "celery_worker_concurrency": settings.celery_worker_concurrency,
        "celery_timezone": settings.celery_timezone,

        # JWT config (no secret)
        "jwt_algorithm": settings.jwt_algorithm,
        "access_token_expire_minutes": settings.access_token_expire_minutes,
        "refresh_token_expire_days": settings.refresh_token_expire_days,

        # API key presence (not the values)
        "api_keys_configured": {
            "anthropic": bool(settings.anthropic_api_key),
            "sendgrid": bool(settings.sendgrid_api_key),
            "telegram": bool(settings.telegram_bot_token),
            "stripe": bool(settings.stripe_secret_key),
            "razorpay": bool(settings.razorpay_key_id),
            "aws": bool(settings.aws_access_key_id),
            "dhan": bool(settings.dhan_client_id),
        },

        # Charts
        "charts_dir": settings.charts_dir,
        "charts_base_url": settings.charts_base_url,
    }
