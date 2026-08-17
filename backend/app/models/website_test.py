from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.database import Base

class WebsiteTest(Base):
    __tablename__ = "website_tests"

    id = Column(Integer, primary_key=True, index=True)

    # Who ran this test, and on which plan — nullable so the older
    # unauthenticated /website/... endpoints still work without a user.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    plan = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    url = Column(String, nullable=False)

    status_code = Column(Integer, default=0)

    response_time = Column(Float, default=0.0)

    ssl_status = Column(String, default="Unknown")

    test_status = Column(String, default="Pending")

    health_score = Column(Integer, default=0)

    seo_score = Column(Integer, default=0)

    accessibility_score = Column(Integer, default=0)

    performance_score = Column(Integer, default=0)

    security_score = Column(Integer, default=0)

    broken_links = Column(Integer, default=0)

    ai_suggestions = Column(Text)

    severity = Column(String, default="Low")

    # Path to the persisted PDF for this specific test run, so the
    # exact report shown at scan-time can be re-downloaded later from
    # history instead of being silently overwritten by the next scan.
    report_path = Column(String, nullable=True)


class FunctionalTestResult(Base):
    __tablename__ = "functional_test_results"

    id = Column(Integer, primary_key=True, index=True)

    url = Column(String, nullable=False)

    functional_score = Column(Integer, default=0)

    total_modules = Column(Integer, default=0)
    executed_modules = Column(Integer, default=0)
    tested_modules = Column(Integer, default=0)

    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    partial = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    not_available = Column(Integer, default=0)

    # Full per-module results (status + issue + failure details like the
    # exact broken link/button/image) stored as JSON text.
    results_json = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())