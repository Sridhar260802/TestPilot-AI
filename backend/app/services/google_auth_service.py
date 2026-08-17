import os

from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


def verify_google_token(token: str) -> dict:
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")

    if not google_client_id:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID is not configured on the server"
        )

    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            google_client_id
        )

        if payload.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            raise ValueError("Invalid token issuer")

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid Google token: {str(e)}"
        )

    if not payload.get("email_verified", False):
        raise HTTPException(
            status_code=401,
            detail="Google account email is not verified"
        )

    return {
        "google_id": payload["sub"],
        "email": payload["email"],
        "name": payload.get("name") or payload["email"].split("@")[0],
        "picture": payload.get("picture"),
    }