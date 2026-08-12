from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), nullable=False)

    email = Column(String(150), unique=True, index=True)

    password = Column(String(255), nullable=False)

    # Subscription tier that gates which testing features the user can run.
    # One of: "basic", "standard", "premium". Defaults to "basic" for new signups.
    plan = Column(String(20), nullable=False, default="basic", server_default="basic")

    created_at = Column(DateTime, default=datetime.utcnow)