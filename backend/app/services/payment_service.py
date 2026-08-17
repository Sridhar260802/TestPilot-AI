from sqlalchemy.orm import Session

from app.models.payment import PaymentTransaction


def create_pending_transaction(
    db: Session, user_id: int, razorpay_order_id: str, plan: str, amount, currency: str
) -> PaymentTransaction:
    transaction = PaymentTransaction(
        user_id=user_id,
        razorpay_order_id=razorpay_order_id,
        plan=plan,
        amount=amount,
        currency=currency,
        status="PENDING",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def get_transaction_by_order_id(db: Session, razorpay_order_id: str):
    return (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.razorpay_order_id == razorpay_order_id)
        .first()
    )


def get_transaction_by_payment_id(db: Session, razorpay_payment_id: str):
    return (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.razorpay_payment_id == razorpay_payment_id)
        .first()
    )


def mark_transaction_success(
    db: Session, transaction: PaymentTransaction, razorpay_payment_id: str, razorpay_signature: str
) -> PaymentTransaction:
    transaction.razorpay_payment_id = razorpay_payment_id
    transaction.razorpay_signature = razorpay_signature
    transaction.status = "SUCCESS"

    db.commit()
    db.refresh(transaction)

    return transaction


def mark_transaction_failed(db: Session, transaction: PaymentTransaction) -> PaymentTransaction:
    transaction.status = "FAILED"

    db.commit()
    db.refresh(transaction)

    return transaction


def get_user_transactions(db: Session, user_id: int):
    return (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.user_id == user_id)
        .order_by(PaymentTransaction.created_at.desc())
        .all()
    )


def get_user_transaction_by_order_id(db: Session, user_id: int, razorpay_order_id: str):
    return (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.user_id == user_id,
            PaymentTransaction.razorpay_order_id == razorpay_order_id,
        )
        .first()
    )
