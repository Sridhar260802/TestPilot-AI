from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.database.dependency import get_db
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserResponse, UserLogin, PlanUpdateRequest
from app.services.user_service import (
    get_user_by_email,
    get_user_by_email_or_username,
    create_user,
    update_user_plan,
)
from app.core.security import hash_password, verify_password
from app.core.jwt_handler import create_access_token

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = get_user_by_email(db, user.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = create_user(
        db=db,
        username=user.username,
        email=user.email,
        password=hashed_password
    )

    return new_user

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    existing_user = get_user_by_email(db, user.email)

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        user.password,
        existing_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": existing_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
@router.get("/me")
def get_current_user_info(current_user= Depends(get_current_user)):
    return {
        "message": "authentication Success",
        "user": current_user
    }   


@router.put("/plan", response_model=UserResponse)
def change_plan(
    data: PlanUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Upgrade/downgrade the current user's subscription tier.
    In a production system this would be driven by a billing webhook
    (e.g. Stripe) instead of being called directly by the client.
    """

    updated_user = update_user_plan(db, current_user, data.plan)

    return updated_user


@router.post("/token")
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    existing_user = get_user_by_email_or_username(
        db,
        form_data.username
    )

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        form_data.password,
        existing_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token({
        "sub": existing_user.email
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }