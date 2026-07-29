from sqlalchemy import Column, Integer, String, Float
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