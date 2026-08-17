from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.orm import Session

from app.core.jwt_handler import SECRET_KEY, ALGORITHM
from app.database.dependency import get_db
from app.services.user_service import get_user_by_email

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/token"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid Token"
            )

    except ExpiredSignatureError:
        # Tokens live for 60 minutes (see jwt_handler.ACCESS_TOKEN_EXPIRE_MINUTES).
        # Surface this distinctly from a malformed/tampered token so the
        # frontend can tell "please log in again" apart from a real bug.
        raise HTTPException(
            status_code=401,
            detail="Session expired. Please log in again."
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Token"
        )

    user = get_user_by_email(db, email)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user