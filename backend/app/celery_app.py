"""
TradeFlow AI — Celery Application Factory
Day 25: Added pipeline tasks + Beat schedule.

Beat schedule fires run_full_pipeline at 06:00 IST (00:30 UTC) daily.
Workers pick tasks off the Redis queue and execute them in parallel.
"""
import os
from celery import Celery
from celery.schedules import crontab

# ---------------------------------------------------------------------------
# Read broker settings from environment
# ---------------------------------------------------------------------------
CELERY_BROKER_URL    = os.getenv(
    "CELERY_BROKER_URL",
    "redis://:tradeflow123@redis:6379/0",
)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://:tradeflow123@redis:6379/1",
)

# ---------------------------------------------------------------------------
# Create the Celery application
# include= tells Celery which modules contain tasks to auto-discover
# ---------------------------------------------------------------------------
celery_app = Celery(
    "tradeflow",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.pipeline",  # Day 25: fetch tasks
        # "app.tasks.alerts",  # Day 29: ops alert tasks
        # "app.tasks.backtest",# Day 53: backtest tasks
        # "app.tasks.signals", # Day 65: AI signal tasks
    ],
)

celery_app.conf.update(
    # ---- Serialisation ----
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # ---- Timezone ----
    # All scheduled times are in IST
    # All stored timestamps are UTC (enable_utc=True)
    timezone="Asia/Kolkata",
    enable_utc=True,

    # ---- Result expiry ----
    # Task results expire after 24 hours — Redis memory management
    result_expires=86400,

    # ---- Task routing ----
    # Different queues for different task types
    # Lets you scale pipeline workers separately from alert workers
    task_routes={
        "app.tasks.pipeline.*": {"queue": "pipeline"},
        "app.tasks.alerts.*":   {"queue": "alerts"},
        "app.tasks.backtest.*": {"queue": "pipeline"},
        "app.tasks.signals.*":  {"queue": "signals"},
    },

    # ---- Reliability settings ----
    # task_acks_late=True:
    #   The task is only "acknowledged" (removed from queue) AFTER it completes.
    #   If the worker crashes mid-task, the task goes back to the queue.
    #   Without this: task is acknowledged on receipt → lost if worker crashes.
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # worker_prefetch_multiplier=1:
    #   Each worker fetches only 1 task at a time.
    #   Without this: a worker grabs 4 tasks, finishes 1, others are idle
    #   while waiting for the greedy worker.
    #   With 1: tasks distributed evenly — better parallelism.
    worker_prefetch_multiplier=1,

    # ---- Beat schedule ----
    # Celery Beat fires these tasks on a cron schedule.
    # Beat runs as a SEPARATE process (celery_beat service in docker-compose).
    beat_schedule={
        # Daily data pipeline — 06:00 IST = 00:30 UTC
        "daily-pipeline-0630-IST": {
            "task":     "app.tasks.pipeline.run_full_pipeline",
            "schedule": crontab(hour=0, minute=30),
            "options":  {"queue": "pipeline"},
        },
        # Future scheduled tasks (uncommented as we build them):
        # "daily-signal-outcomes": {
        #     "task":     "app.tasks.pipeline.check_signal_outcomes",
        #     "schedule": crontab(hour=1, minute=0),
        # },
        # "daily-fetch-failure-alert": {
        #     "task":     "app.tasks.alerts.check_fetch_failures",
        #     "schedule": crontab(hour=1, minute=30),
        # },
    },
)

# Export as "app" so the Celery CLI command works:
#   celery -A app.celery_app worker
app = celery_app
