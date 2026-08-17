from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), nullable=False)

    email = Column(String(150), unique=True, index=True)

    # Nullable now: Google sign-in users have no local password.
    password = Column(String(255), nullable=True)

    # "local" for email/password signups, "google" for Google sign-in.
    auth_provider = Column(String(20), nullable=False, default="local", server_default="local")

    # Google's stable per-account id ("sub" claim). Unique when present.
    google_id = Column(String(255), unique=True, index=True, nullable=True)

    # Profile picture URL returned by Google, if any.
    picture = Column(String(500), nullable=True)

    # Subscription tier that gates which testing features the user can run.
    # One of: "basic", "standard", "premium". NULL/None until the user
    # actually pays for a plan via PUT /users/plan - new signups and
    # Google sign-ins are never auto-assigned a plan.
    plan = Column(String(20), nullable=True, default=None)

    created_at = Column(DateTime, default=datetime.utcnow)