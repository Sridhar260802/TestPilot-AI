from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class PaymentTransaction(Base):
    """
    One row per Razorpay order created for a user. Created as PENDING when
    the order is created, then updated to SUCCESS once /payments/verify
    validates the Razorpay signature. This table only tracks payment
    status - it does not activate plans or credits (that stays in the
    existing subscription/credit system, untouched by this file).
    """

    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    razorpay_order_id = Column(String(64), unique=True, index=True, nullable=False)
    razorpay_payment_id = Column(String(64), unique=True, index=True, nullable=True)
    razorpay_signature = Column(String(255), nullable=True)

    plan = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # rupees, e.g. 399.00
    currency = Column(String(10), nullable=False, default="INR", server_default="INR")

    # PENDING -> SUCCESS, or FAILED if verification was attempted and failed.
    status = Column(String(20), nullable=False, default="PENDING", server_default="PENDING")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
