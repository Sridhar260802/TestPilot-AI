from sqlalchemy import Column, Integer, ForeignKey
from app.database.database import Base


class DashboardStats(Base):
    __tablename__ = "dashboard_stats"

    id = Column(Integer, primary_key=True, index=True)

    # Each user gets their own stats row. Nullable only so legacy/anonymous
    # (not-logged-in) test endpoints still have somewhere to write counts;
    # every authenticated flow always sets this.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    total_tests = Column(Integer, default=0)
    website_tests = Column(Integer, default=0)
    code_analysis = Column(Integer, default=0)
    mobile_tests = Column(Integer, default=0)

    ai_suggestions = Column(Integer, default=0)
    reports_generated = Column(Integer, default=0)

    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)