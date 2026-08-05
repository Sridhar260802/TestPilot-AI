from sqlalchemy import Column, Integer, String, Float, Text
from app.database.database import Base

class WebsiteTest(Base):
    __tablename__ = "website_tests"

    id = Column(Integer, primary_key=True, index=True)

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