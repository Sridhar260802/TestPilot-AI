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


def create_user(db: Session, username: str, email: str, password: str):
    user = User(
        username=username,
        email=email,
        password=password,
        plan="basic"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user_plan(db: Session, user: User, plan: str):
    user.plan = plan

    db.commit()
    db.refresh(user)

    return user