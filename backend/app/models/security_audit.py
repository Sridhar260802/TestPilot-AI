from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class SecurityAudit(Base):
    __tablename__ = "security_audits"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    url = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False)
    security_score = Column(Integer, default=0)
    issue = Column(Text, nullable=True)
    possible_reason = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    developer_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)