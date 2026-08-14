"""
TradeFlow AI — User & Auth Models
Day 11: User, AuthToken, ApiKey, BrokerCredential

These 4 models are the auth foundation.
Every other model (signals, watchlist, billing etc.) links back to User.

Security rules baked into this design:
- Passwords NEVER stored as plaintext — only bcrypt hashes
- API keys NEVER stored as plaintext — only bcrypt hashes
- Broker credentials NEVER stored as plaintext — AES-256 encrypted
- Refresh tokens stored as hashes — revocable at any time
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    Every human who uses TradeFlow AI.

    Plan tiers: "free", "pro", "business"
    - free     → 3 watchlist symbols, basic signals
    - pro      → unlimited symbols, all strategies
    - business → API access, on-demand backtests, REST webhook

    Notification settings stored here so we know WHERE to send signals:
    - email_notifications → daily digest via SendGrid
    - telegram_chat_id   → per-signal via Telegram bot
    - slack_webhook_url  → per-signal via Slack
    - rest_webhook_url   → per-signal via custom endpoint (Business only)
    """
    __tablename__ = "users"

    # ---------------------------------------------------------------------------
    # Primary Key
    # ---------------------------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ---------------------------------------------------------------------------
    # Identity
    # ---------------------------------------------------------------------------
    email = Column(
        String(255),
        nullable=False,
        unique=True,        # no two users can share an email
        index=True,         # login queries filter by email — needs index
        comment="User's email address — used for login and notifications",
    )

    # NEVER store plaintext passwords — only the bcrypt hash
    # bcrypt hash always starts with "$2b$12$..."
    # We verify by calling: bcrypt.verify(plain_password, hashed_password)
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="bcrypt hash of the password — NEVER the plaintext",
    )

    full_name = Column(String(255), nullable=True)

    # ---------------------------------------------------------------------------
    # Account status
    # ---------------------------------------------------------------------------
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="False = account disabled (banned or deactivated)",
    )
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True only after email verification link is clicked",
    )

    # ---------------------------------------------------------------------------
    # Subscription plan
    # ---------------------------------------------------------------------------
    plan = Column(
        String(20),
        default="free",
        nullable=False,
        comment="free | pro | business",
    )

    # ---------------------------------------------------------------------------
    # Notification channels
    # Each can be toggled independently
    # ---------------------------------------------------------------------------
    email_notifications = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Send daily signal digest via email",
    )
    telegram_chat_id = Column(
        String(50),
        nullable=True,
        comment="Telegram chat ID — linked via bot deep link",
    )
    telegram_notifications = Column(
        Boolean,
        default=False,
        nullable=False,
    )
    slack_webhook_url = Column(
        Text,
        nullable=True,
        comment="User's Slack Incoming Webhook URL",
    )
    slack_notifications = Column(
        Boolean,
        default=False,
        nullable=False,
    )
    rest_webhook_url = Column(
        Text,
        nullable=True,
        comment="Custom HTTPS endpoint for Business tier signal delivery",
    )
    rest_webhook_secret = Column(
        String(255),
        nullable=True,
        comment="HMAC-SHA256 signing secret for webhook verification",
    )

    # ---------------------------------------------------------------------------
    # Timestamps
    # ---------------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=datetime.utcnow,   # auto-updates when row is modified
        nullable=True,
    )

    # ---------------------------------------------------------------------------
    # Relationships
    # These let us write: user.auth_tokens, user.api_keys etc.
    # cascade="all, delete-orphan" means:
    #   if we delete a User, all their tokens/keys are also deleted
    #   (matches the ON DELETE CASCADE on the foreign key)
    # ---------------------------------------------------------------------------
    auth_tokens = relationship(
        "AuthToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    api_keys = relationship(
        "ApiKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    broker_credentials = relationship(
        "BrokerCredential",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} plan={self.plan}>"


class AuthToken(Base):
    """
    Refresh tokens — stored so they can be revoked.

    Why store refresh tokens?
    JWT access tokens are self-contained — you can't invalidate them
    before they expire (15 minutes). But refresh tokens can be deleted
    from this table, making them immediately invalid.

    On logout: delete the row from this table.
    On refresh: find the row, issue new tokens, delete old row (rotation).

    We store a HASH of the token, not the token itself.
    If someone reads the database, they can't use the hashes to log in.
    """
    __tablename__ = "auth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which user does this token belong to?
    # ON DELETE CASCADE: if User is deleted, all their tokens are too
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SHA-256 hash of the actual refresh token string
    # We hash it so a DB breach doesn't expose usable tokens
    token_hash = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hash of the refresh token",
    )

    # When does this token expire? (30 days from creation)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Soft revocation — can mark as revoked without deleting
    # Useful for audit logs (knowing a token was revoked vs expired)
    revoked = Column(Boolean, default=False, nullable=False)

    # Back-reference to User
    user = relationship("User", back_populates="auth_tokens")

    def __repr__(self) -> str:
        return f"<AuthToken user={self.user_id} revoked={self.revoked}>"


class ApiKey(Base):
    """
    API keys for Business tier users — programmatic access.

    How it works:
    1. User clicks "Generate API Key" in settings
    2. We generate a random 32-byte key: `secrets.token_hex(32)`
    3. We SHOW it to the user ONCE (they must save it themselves)
    4. We store only the BCRYPT HASH in this table
    5. On each request with X-API-Key header:
       - Find all active keys for the user
       - bcrypt.verify(incoming_key, stored_hash)
       - If match → authenticated

    Why bcrypt for API keys?
    Same reason as passwords — if DB is breached, attacker
    can't use hashes to authenticate.
    """
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # bcrypt hash of the actual API key
    key_hash = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="bcrypt hash of the API key — NEVER stored in plaintext",
    )

    # Human-readable name so user knows which key is which
    # e.g. "My Trading Bot", "Laptop", "Production Server"
    name = Column(String(100), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Updated every time the key is used in a request
    # Tells user "this key was last used on X" — security visibility
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # False = key is revoked (user deleted it from settings)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<ApiKey '{self.name}' user={self.user_id} active={self.is_active}>"


class BrokerCredential(Base):
    """
    Broker API credentials — AES-256 encrypted at rest.

    Used for:
    - Live equity tick streaming (Dhan, Fyers, Angel One)
    - Live order placement (Day 143 — Zerodha, Angel One, IBKR)

    Security:
    - Credentials are encrypted with Fernet (AES-128-CBC + HMAC)
    - The encryption key lives ONLY in the environment variable
    - If the DB is compromised, credentials are unreadable ciphertext
    - The API never returns the actual credentials — only confirms they exist

    user_id=None means it's a "house feed" account (ops team's account
    used for the pipeline data feed, not a user's trading account).
    """
    __tablename__ = "broker_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # nullable=True allows house feed accounts (no user)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Which broker: "dhan", "fyers", "angelone", "zerodha", "ibkr"
    broker_name = Column(String(50), nullable=False)

    # Fernet-encrypted ciphertext — stored as base64 string
    encrypted_api_key = Column(
        Text,
        nullable=False,
        comment="Fernet(AES) encrypted API key — NOT plaintext",
    )
    encrypted_access_token = Column(
        Text,
        nullable=False,
        comment="Fernet(AES) encrypted access token — NOT plaintext",
    )

    linked_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="broker_credentials")

    def __repr__(self) -> str:
        return f"<BrokerCredential {self.broker_name} user={self.user_id}>"
