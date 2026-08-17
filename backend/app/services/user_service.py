from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_email_or_username(db: Session, identifier: str):
    return (
        db.query(User)
        .filter((User.email == identifier) | (User.username == identifier))
        .first()
    )


def get_user_by_google_id(db: Session, google_id: str):
    return db.query(User).filter(User.google_id == google_id).first()


def create_user(db: Session, username: str, email: str, password: str):
    # No plan is assigned at signup - the user only gets a plan once they
    # actually pay for one (see PUT /users/plan / update_user_plan below).
    user = User(
        username=username,
        email=email,
        password=password,
        auth_provider="local",
        plan="NO Active Plan"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_google_user(db: Session, email: str, username: str, google_id: str, picture: str = None):
    # Same as create_user: Google sign-in does not auto-assign a plan either.
    user = User(
        username=username,
        email=email,
        password=None,
        auth_provider="google",
        google_id=google_id,
        picture=picture,
        plan="NO Active Plan"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def link_google_account(db: Session, user: User, google_id: str, picture: str = None):
    """
    An account with this email already exists (created via normal signup).
    Link the Google identity to it instead of creating a duplicate row,
    so the person can sign in either way afterwards.
    """
    user.google_id = google_id

    if picture and not user.picture:
        user.picture = picture

    db.commit()
    db.refresh(user)

    return user


def update_user_plan(db: Session, user: User, plan: str):
    user.plan = plan

    db.commit()
    db.refresh(user)

    return user