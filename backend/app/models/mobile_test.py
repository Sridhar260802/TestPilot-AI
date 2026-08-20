from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.database import Base


class MobileAppTest(Base):
    __tablename__ = "mobile_app_tests"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    plan = Column(String, nullable=True)
    scan_depth = Column(String, nullable=True)  # basic | standard | premium

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    platform = Column(String, nullable=False)  # android | ios
    file_name = Column(String, nullable=False)
    package_or_bundle_id = Column(String, nullable=True)
    app_version = Column(String, nullable=True)

    security_score = Column(Integer, default=0)
    severity = Column(String, default="Low")
    issue_count = Column(Integer, default=0)

    # Full analysis result (overview, permissions, exported components,
    # secret/crypto scan, etc.) stored as JSON text, same pattern as
    # WebsiteTest.ai_suggestions.
    result_json = Column(Text)

    report_path = Column(String, nullable=True)