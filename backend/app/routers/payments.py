from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.plans import PLAN_PRICES
from app.database.dependency import get_db
from app.models.user import User
from app.schemas.payment import (
    CreateOrderRequest,
    CreateOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    PaymentHistoryItem,
    PaymentStatusResponse,
)
from app.services.payment_service import (
    create_pending_transaction,
    get_transaction_by_payment_id,
    mark_transaction_success,
    get_user_transactions,
    get_user_transaction_by_order_id,
)
from app.services.razorpay_service import create_razorpay_order, verify_payment_signature

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(
    data: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a Razorpay order for the given plan. The amount is always
    looked up server-side from PLAN_PRICES (app/core/plans.py) - the
    frontend only ever sends the plan name, never an amount.

    This only creates the order/payment record. It does NOT activate the
    user's plan or credits - that happens separately, after /payments/verify
    confirms payment, through your existing subscription/credit system.
    """

    plan = data.plan.lower()

    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Invalid plan '{data.plan}'.")

    amount_rupees = PLAN_PRICES[plan]
    amount_paise = int(amount_rupees) * 100
    currency = "INR"

    order = create_razorpay_order(
        amount_paise=amount_paise,
        currency=currency,
        receipt=f"user_{current_user.id}_{plan}",
        notes={"user_id": str(current_user.id), "plan": plan},
    )

    create_pending_transaction(
        db=db,
        user_id=current_user.id,
        razorpay_order_id=order["id"],
        plan=plan,
        amount=amount_rupees,
        currency=currency,
    )

    return {
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": currency,
        "plan": plan,
    }


@router.post("/verify", response_model=VerifyPaymentResponse)
def verify_payment(
    data: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verifies a Razorpay Checkout payment using Razorpay's official
    signature verification. Only marks the transaction SUCCESS - does NOT
    activate the user's plan or credits (your existing subscription/credit
    system handles that separately).
    """

    transaction = get_user_transaction_by_order_id(db, current_user.id, data.razorpay_order_id)

    if transaction is None:
        raise HTTPException(status_code=404, detail="Order not found for this user.")

    # Duplicate payment protection: this order was already verified -
    # return the existing result instead of re-processing it.
    if transaction.status == "SUCCESS":
        return {
            "order_id": transaction.razorpay_order_id,
            "payment_id": transaction.razorpay_payment_id,
            "plan": transaction.plan,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "status": transaction.status,
        }

    # Duplicate payment protection: this razorpay_payment_id was already
    # used to complete a *different* order - reject as a conflict rather
    # than letting it overwrite another transaction.
    existing_for_payment = get_transaction_by_payment_id(db, data.razorpay_payment_id)
    if existing_for_payment is not None and existing_for_payment.id != transaction.id:
        raise HTTPException(status_code=409, detail="This payment has already been processed.")

    is_valid = verify_payment_signature(
        order_id=data.razorpay_order_id,
        payment_id=data.razorpay_payment_id,
        signature=data.razorpay_signature,
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature.")

    transaction = mark_transaction_success(
        db,
        transaction,
        razorpay_payment_id=data.razorpay_payment_id,
        razorpay_signature=data.razorpay_signature,
    )

    return {
        "order_id": transaction.razorpay_order_id,
        "payment_id": transaction.razorpay_payment_id,
        "plan": transaction.plan,
        "amount": float(transaction.amount),
        "currency": transaction.currency,
        "status": transaction.status,
    }


@router.get("/history", response_model=list[PaymentHistoryItem])
def payment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns only the logged-in user's own payment records."""

    transactions = get_user_transactions(db, current_user.id)

    return [
        {
            "order_id": t.razorpay_order_id,
            "payment_id": t.razorpay_payment_id,
            "plan": t.plan,
            "amount": float(t.amount),
            "currency": t.currency,
            "status": t.status,
            "created_at": t.created_at,
        }
        for t in transactions
    ]


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
def payment_status(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the payment status for `order_id`, only if that order belongs
    to the logged-in user (never another user's order).
    """

    transaction = get_user_transaction_by_order_id(db, current_user.id, order_id)

    if transaction is None:
        raise HTTPException(status_code=404, detail="Order not found for this user.")

    return {
        "order_id": transaction.razorpay_order_id,
        "payment_id": transaction.razorpay_payment_id,
        "plan": transaction.plan,
        "amount": float(transaction.amount),
        "currency": transaction.currency,
        "status": transaction.status,
        "created_at": transaction.created_at,
        "updated_at": transaction.updated_at,
    }
