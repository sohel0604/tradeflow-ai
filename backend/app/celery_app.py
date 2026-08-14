"""
TradeFlow AI — Celery Application
Day 7: Minimal skeleton — connects to Redis broker.
We add real tasks from Day 31 onwards.
"""
import os
from celery import Celery

# ---------------------------------------------------------------------------
# Read broker URL from environment variable
# Falls back to local Redis if not set
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://:tradeflow123@redis:6379/0"
)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://:tradeflow123@redis:6379/1"
)

# ---------------------------------------------------------------------------
# Create the Celery app
# "tradeflow" is the app name — appears in Flower dashboard
# include= lists task modules Celery will discover
# We add task modules here as we build them day by day
# ---------------------------------------------------------------------------
celery_app = Celery(
    "tradeflow",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        # "app.tasks.pipeline",   ← added Day 32
        # "app.tasks.alerts",     ← added Day 36
        # "app.tasks.backtest",   ← added Day 53
        # "app.tasks.signals",    ← added Day 65
    ],
)

celery_app.conf.update(
    # Always use JSON — human readable, language agnostic
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone — all scheduled tasks run in IST
    timezone="Asia/Kolkata",
    enable_utc=True,

    # Results expire after 24 hours — don't fill up Redis
    result_expires=86400,

    # Reliability settings
    # acks_late: task is only marked done AFTER it completes
    # If worker crashes mid-task, task is re-queued
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Fetch one task at a time — prevents one worker hogging all tasks
    worker_prefetch_multiplier=1,
)

# Make importable as "app" for the celery CLI command:
# celery -A app.celery_app worker
app = celery_app
