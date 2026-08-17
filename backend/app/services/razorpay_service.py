import os

import razorpay
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

# Set these in your .env file. Get them from the Razorpay Dashboard ->
# Settings -> API Keys. Never commit real keys to Git.
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


def _get_client() -> razorpay.Client:
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        # Don't leak which one is missing or any part of the value - just
        # tell the caller payments aren't configured on the server yet.
        raise HTTPException(
            status_code=500,
            detail="Payments are not configured on the server.",
        )
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_razorpay_order(amount_paise: int, currency: str, receipt: str, notes: dict) -> dict:
    """
    Creates a Razorpay order for `amount_paise` (integer, smallest currency
    unit - paise for INR). Returns the raw Razorpay order dict (contains
    "id", "amount", "currency", "status", ...).
    """
    client = _get_client()
    try:
        return client.order.create({
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1,
            "notes": notes,
        })
    except razorpay.errors.BadRequestError as e:
        raise HTTPException(status_code=400, detail=f"Could not create Razorpay order: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Could not create Razorpay order.")


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verifies a Razorpay Checkout payment using Razorpay's official
    signature verification (HMAC-SHA256 over "order_id|payment_id" keyed
    with RAZORPAY_KEY_SECRET). Returns True if valid, False if invalid.
    """
    client = _get_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
