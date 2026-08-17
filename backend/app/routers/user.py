from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.database.dependency import get_db
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserResponse, UserLogin, PlanUpdateRequest, GoogleLoginRequest, GoogleLoginResponse
from app.services.user_service import (
    get_user_by_email,
    get_user_by_email_or_username,
    get_user_by_google_id,
    create_user,
    create_google_user,
    link_google_account,
    update_user_plan,
)
from app.core.security import hash_password, verify_password
from app.core.jwt_handler import create_access_token
from app.services.google_auth_service import verify_google_token

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
@router.post("/google", response_model=GoogleLoginResponse)
def google_login(data: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Sign in / sign up with Google.
    Frontend sends the Google ID token here; we verify it with Google,
    find-or-create the matching user row, and return our own JWT
    (same shape as /users/login) so the rest of the app is unaffected.
    """
    google_info = verify_google_token(data.token)

    user = get_user_by_google_id(db, google_info["google_id"])

    if not user:
        # No account linked to this Google id yet. Check if an account
        # with this email already exists (e.g. they signed up normally
        # before) and link it instead of creating a duplicate.
        existing_by_email = get_user_by_email(db, google_info["email"])

        if existing_by_email:
            user = link_google_account(
                db,
                existing_by_email,
                google_id=google_info["google_id"],
                picture=google_info["picture"]
            )
        else:
            user = create_google_user(
                db,
                email=google_info["email"],
                username=google_info["name"],
                google_id=google_info["google_id"],
                picture=google_info["picture"]
            )

    access_token = create_access_token({"sub": user.email})

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "plan": user.plan,
        "auth_provider": user.auth_provider,
        "picture": user.picture,
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