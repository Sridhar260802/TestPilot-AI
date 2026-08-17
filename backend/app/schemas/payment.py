from datetime import datetime

from pydantic import BaseModel


class CreateOrderRequest(BaseModel):
    # Plain str (not a Literal) so an invalid plan is validated manually in
    # the router and returned as a clean 400, not FastAPI's default 422.
    plan: str


class CreateOrderResponse(BaseModel):
    order_id: str
    # Amount in paise (smallest INR unit) - this is what the Razorpay
    # Checkout script on the frontend expects for its "amount" option.
    amount: int
    currency: str
    plan: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    order_id: str
    payment_id: str
    plan: str
    amount: float
    currency: str
    status: str


class PaymentHistoryItem(BaseModel):
    order_id: str
    payment_id: str | None = None
    plan: str
    amount: float
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentStatusResponse(BaseModel):
    order_id: str
    payment_id: str | None = None
    plan: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime | None = None
