from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database.database import Base


class CodeAnalysis(Base):

    __tablename__ = "code_analysis"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    filename = Column(
        String
    )


    language = Column(
        String
    )


    score = Column(
        Integer
    )


    issues = Column(
        Text
    )


    severity = Column(
        Text
    )


    ai_suggestions = Column(
        Text
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )