"""
Alembic env.py — Migration Environment
Day 13: Connects Alembic to our SQLAlchemy models and database.

This file runs every time you run an alembic command.
It tells Alembic:
1. Which database to connect to (from our settings)
2. Which models to track (our Base.metadata)
3. How to run migrations (online = real DB, offline = SQL script)
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Add the backend folder to Python path
# This lets us import from app/ inside the migration scripts
# ---------------------------------------------------------------------------
# /app/alembic/env.py → we need /app on the path to import app.models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Import our models and settings
# IMPORTANT: importing app.models loads ALL models into Base.metadata
# Alembic reads Base.metadata to know what tables to create/modify
# ---------------------------------------------------------------------------
from app.core.config import settings   # noqa: E402
from app.core.database import Base     # noqa: E402
import app.models                      # noqa: F401, E402 — registers all models

# ---------------------------------------------------------------------------
# Alembic Config — reads alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Override the database URL from our settings
# (instead of the hardcoded one in alembic.ini)
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is the Base.metadata that Alembic compares against the live DB
# It knows ALL tables because we imported app.models above
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# run_migrations_offline()
# Generates a SQL script instead of connecting to the DB
# Useful for: reviewing migrations before applying, CI pipelines
# Usage: alembic upgrade head --sql > migration.sql
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,           # detect column type changes
        compare_server_default=True, # detect default value changes
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# run_migrations_online()
# Connects to the real database and applies migrations directly
# This is the normal mode — what runs when you do `alembic upgrade head`
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    # Create a synchronous engine (Alembic doesn't support async)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # NullPool: don't keep connections open
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Run in the correct mode
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
