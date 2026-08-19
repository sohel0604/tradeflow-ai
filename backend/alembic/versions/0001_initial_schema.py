"""Initial schema — all 14 tables

Revision ID: 0001
Revises:
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # =========================================================================
    # users — must be first (other tables reference it)
    # =========================================================================
    op.create_table(
        "users",
        sa.Column("id",                   postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email",                sa.String(255),  nullable=False),
        sa.Column("hashed_password",      sa.String(255),  nullable=False),
        sa.Column("full_name",            sa.String(255),  nullable=True),
        sa.Column("is_active",            sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("is_verified",          sa.Boolean(),    nullable=False, server_default="false"),
        sa.Column("plan",                 sa.String(20),   nullable=False, server_default="free"),
        sa.Column("email_notifications",  sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("telegram_chat_id",     sa.String(50),   nullable=True),
        sa.Column("telegram_notifications", sa.Boolean(),  nullable=False, server_default="false"),
        sa.Column("slack_webhook_url",    sa.Text(),       nullable=True),
        sa.Column("slack_notifications",  sa.Boolean(),    nullable=False, server_default="false"),
        sa.Column("rest_webhook_url",     sa.Text(),       nullable=True),
        sa.Column("rest_webhook_secret",  sa.String(255),  nullable=True),
        sa.Column("created_at",           sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at",           sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # =========================================================================
    # price_bars
    # =========================================================================
    op.create_table(
        "price_bars",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol",     sa.String(50),  nullable=False),
        sa.Column("timeframe",  sa.String(10),  nullable=False),
        sa.Column("timestamp",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("open",       sa.Float(),     nullable=False),
        sa.Column("high",       sa.Float(),     nullable=False),
        sa.Column("low",        sa.Float(),     nullable=False),
        sa.Column("close",      sa.Float(),     nullable=False),
        sa.Column("volume",     sa.Float(),     nullable=False, server_default="0"),
        sa.Column("asset_type", sa.String(20),  nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("symbol", "timeframe", "timestamp",
                            name="uq_price_bars_symbol_tf_ts"),
    )
    op.create_index("ix_price_bars_symbol_timeframe", "price_bars", ["symbol", "timeframe"])
    op.create_index("ix_price_bars_timestamp",        "price_bars", ["timestamp"])
    op.create_index("ix_price_bars_asset_type",       "price_bars", ["asset_type"])

    # =========================================================================
    # fetch_logs
    # =========================================================================
    op.create_table(
        "fetch_logs",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol",     sa.String(50),  nullable=False),
        sa.Column("timeframe",  sa.String(10),  nullable=False),
        sa.Column("status",     sa.String(20),  nullable=False),
        sa.Column("rows_saved", sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("error_msg",  sa.Text(),      nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source",     sa.String(20),  nullable=False, server_default="yfinance"),
    )
    op.create_index("ix_fetch_logs_symbol_status", "fetch_logs", ["symbol", "status"])
    op.create_index("ix_fetch_logs_fetched_at",    "fetch_logs", ["fetched_at"])

    # =========================================================================
    # auth_tokens
    # =========================================================================
    op.create_table(
        "auth_tokens",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",     postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash",  sa.String(255), nullable=False),
        sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked",     sa.Boolean(),   nullable=False, server_default="false"),
    )
    op.create_index("ix_auth_tokens_user_id",    "auth_tokens", ["user_id"])
    op.create_index("ix_auth_tokens_token_hash", "auth_tokens", ["token_hash"], unique=True)

    # =========================================================================
    # api_keys
    # =========================================================================
    op.create_table(
        "api_keys",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",      postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash",     sa.String(255), nullable=False),
        sa.Column("name",         sa.String(100), nullable=False),
        sa.Column("created_at",   sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active",    sa.Boolean(),   nullable=False, server_default="true"),
    )
    op.create_index("ix_api_keys_user_id",  "api_keys", ["user_id"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    # =========================================================================
    # broker_credentials
    # =========================================================================
    op.create_table(
        "broker_credentials",
        sa.Column("id",                      postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",                 postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("broker_name",             sa.String(50), nullable=False),
        sa.Column("encrypted_api_key",       sa.Text(),     nullable=False),
        sa.Column("encrypted_access_token",  sa.Text(),     nullable=False),
        sa.Column("linked_at",               sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active",               sa.Boolean(),  nullable=False, server_default="true"),
    )
    op.create_index("ix_broker_credentials_user_id", "broker_credentials", ["user_id"])

    # =========================================================================
    # user_watchlist
    # =========================================================================
    op.create_table(
        "user_watchlist",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",    postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol",     sa.String(50), nullable=False),
        sa.Column("asset_type", sa.String(20), nullable=False),
        sa.Column("added_at",   sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "symbol", name="uq_watchlist_user_symbol"),
    )
    op.create_index("ix_watchlist_user_id", "user_watchlist", ["user_id"])

    # =========================================================================
    # subscriptions
    # =========================================================================
    op.create_table(
        "subscriptions",
        sa.Column("id",                       postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",                  postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan",                     sa.String(20), nullable=False),
        sa.Column("status",                   sa.String(20), nullable=False, server_default="active"),
        sa.Column("provider",                 sa.String(20), nullable=True),
        sa.Column("provider_subscription_id", sa.Text(),     nullable=True),
        sa.Column("provider_customer_id",     sa.Text(),     nullable=True),
        sa.Column("current_period_start",     sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end",       sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end",     sa.Boolean(),  nullable=False, server_default="false"),
        sa.Column("created_at",               sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at",               sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    # =========================================================================
    # signals
    # =========================================================================
    op.create_table(
        "signals",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol",          sa.String(50),  nullable=False),
        sa.Column("strategy",        sa.String(100), nullable=False),
        sa.Column("signal_date",     sa.DateTime(timezone=True), nullable=False),
        sa.Column("direction",       sa.String(10),  nullable=False),
        sa.Column("entry_price",     sa.Float(),     nullable=True),
        sa.Column("stop_loss",       sa.Float(),     nullable=True),
        sa.Column("take_profit_1",   sa.Float(),     nullable=True),
        sa.Column("take_profit_2",   sa.Float(),     nullable=True),
        sa.Column("confidence",      sa.Float(),     nullable=True),
        sa.Column("reasoning",       sa.Text(),      nullable=True),
        sa.Column("win_rate",        sa.Float(),     nullable=True),
        sa.Column("avg_rr",          sa.Float(),     nullable=True),
        sa.Column("chart_image_url", sa.Text(),      nullable=True),
        sa.Column("outcome",         sa.String(10),  nullable=False, server_default="OPEN"),
        sa.Column("pattern_tags",    postgresql.JSON(), nullable=True),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at",      sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("symbol", "strategy", "signal_date",
                            name="uq_signal_symbol_strategy_date"),
    )
    op.create_index("ix_signals_symbol_date", "signals", ["symbol", "signal_date"])
    op.create_index("ix_signals_direction",   "signals", ["direction"])
    op.create_index("ix_signals_outcome",     "signals", ["outcome"])

    # =========================================================================
    # backtest_results
    # =========================================================================
    op.create_table(
        "backtest_results",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol",        sa.String(50),  nullable=False),
        sa.Column("strategy",      sa.String(100), nullable=False),
        sa.Column("run_date",      sa.DateTime(timezone=True), nullable=False),
        sa.Column("win_rate",      sa.Float(),     nullable=True),
        sa.Column("avg_rr",        sa.Float(),     nullable=True),
        sa.Column("sharpe_ratio",  sa.Float(),     nullable=True),
        sa.Column("max_drawdown",  sa.Float(),     nullable=True),
        sa.Column("profit_factor", sa.Float(),     nullable=True),
        sa.Column("total_trades",  sa.Integer(),   nullable=False, server_default="0"),
        sa.Column("passed",        sa.Boolean(),   nullable=False, server_default="false"),
        sa.Column("parameters",    postgresql.JSON(), nullable=True),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("symbol", "strategy", "run_date",
                            name="uq_backtest_symbol_strategy_date"),
    )
    op.create_index("ix_backtest_symbol_strategy", "backtest_results", ["symbol", "strategy"])
    op.create_index("ix_backtest_passed",          "backtest_results", ["passed"])
    op.create_index("ix_backtest_run_date",        "backtest_results", ["run_date"])

    # =========================================================================
    # user_strategy_configs
    # =========================================================================
    op.create_table(
        "user_strategy_configs",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",         postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("strategy_name",   sa.String(100), nullable=False),
        sa.Column("parameters_json", postgresql.JSON(), nullable=False),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at",      sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "strategy_name", name="uq_user_strategy_config"),
    )

    # =========================================================================
    # paper_portfolios
    # =========================================================================
    op.create_table(
        "paper_portfolios",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",          postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starting_balance", sa.Float(), nullable=False, server_default="100000"),
        sa.Column("current_balance",  sa.Float(), nullable=False, server_default="100000"),
        sa.Column("is_active",        sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_paper_portfolios_user_id", "paper_portfolios", ["user_id"])

    # =========================================================================
    # paper_positions
    # =========================================================================
    op.create_table(
        "paper_positions",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",       postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("portfolio_id",  postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("paper_portfolios.id"), nullable=False),
        sa.Column("signal_id",     postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("signals.id"), nullable=True),
        sa.Column("symbol",        sa.String(50),  nullable=False),
        sa.Column("direction",     sa.String(10),  nullable=False),
        sa.Column("entry_price",   sa.Float(),     nullable=False),
        sa.Column("quantity",      sa.Float(),     nullable=False),
        sa.Column("stop_loss",     sa.Float(),     nullable=True),
        sa.Column("take_profit_1", sa.Float(),     nullable=True),
        sa.Column("take_profit_2", sa.Float(),     nullable=True),
        sa.Column("opened_at",     sa.DateTime(timezone=True), nullable=False),
        sa.Column("status",        sa.String(10),  nullable=False, server_default="OPEN"),
    )
    op.create_index("ix_paper_positions_user_status", "paper_positions", ["user_id", "status"])

    # =========================================================================
    # paper_trades
    # =========================================================================
    op.create_table(
        "paper_trades",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("position_id",  postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("paper_positions.id"), nullable=False),
        sa.Column("user_id",      postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol",       sa.String(50),  nullable=False),
        sa.Column("direction",    sa.String(10),  nullable=False),
        sa.Column("entry_price",  sa.Float(),     nullable=False),
        sa.Column("exit_price",   sa.Float(),     nullable=False),
        sa.Column("quantity",     sa.Float(),     nullable=False),
        sa.Column("pnl",          sa.Float(),     nullable=False),
        sa.Column("opened_at",    sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at",    sa.DateTime(timezone=True), nullable=False),
        sa.Column("exit_reason",  sa.String(20),  nullable=False),
    )
    op.create_index("ix_paper_trades_user_id", "paper_trades", ["user_id"])


def downgrade() -> None:
    # Drop in reverse order (child tables before parent tables)
    op.drop_table("paper_trades")
    op.drop_table("paper_positions")
    op.drop_table("paper_portfolios")
    op.drop_table("user_strategy_configs")
    op.drop_table("backtest_results")
    op.drop_table("signals")
    op.drop_table("subscriptions")
    op.drop_table("user_watchlist")
    op.drop_table("broker_credentials")
    op.drop_table("api_keys")
    op.drop_table("auth_tokens")
    op.drop_table("fetch_logs")
    op.drop_table("price_bars")
    op.drop_table("users")
