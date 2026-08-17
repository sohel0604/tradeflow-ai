"""
TradeFlow AI — Billing Model
Day 12: Subscription

Tracks the user's active subscription.
Payments are processed by Stripe (international) or Razorpay (India).
We NEVER store card numbers — Stripe/Razorpay handle that.
We only store the provider's IDs so we can:
- Check subscription status
- Handle renewals and cancellations
- Issue refunds via the provider's API
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime,
    ForeignKey, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Subscription(Base):
    """
    One active subscription per user.

    status values:
    - active     → currently paying, full access
    - cancelled  → will downgrade at period_end
    - past_due   → payment failed, grace period
    - expired    → grace period ended, back to free

    plan values:
    - free       → default for new users
    - pro        → INR 999/month
    - business   → INR 3,999/month
    """
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan   = Column(String(20), nullable=False, comment="free | pro | business")
    status = Column(
        String(20),
        default="active",
        nullable=False,
        comment="active | cancelled | past_due | expired",
    )

    # Which payment provider processed this subscription
    provider = Column(
        String(20),
        nullable=True,
        comment="stripe | razorpay",
    )

    # Provider's IDs — used to look up the subscription in their dashboard
    provider_subscription_id = Column(Text, nullable=True)
    provider_customer_id      = Column(Text, nullable=True)

    # Current billing period
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end   = Column(DateTime(timezone=True), nullable=True)

    # True when user has clicked "Cancel" — stays active until period_end
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<Subscription {self.plan} {self.status} "
            f"user={self.user_id}>"
        )
