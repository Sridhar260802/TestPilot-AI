from sqlalchemy.orm import Session
from app.models.website_test import WebsiteTest

def save_website_test(db: Session, url: str, result: dict):
    website = WebsiteTest(
        url=url,
        status_code=result["status_code"],
        response_time=result["response_time"],
        ssl_status=result["ssl_status"],
        test_status=result["test_status"]
    )

    db.add(website)
    db.commit()
    db.refresh(website)

    return website

def get_all_website_tests(db: Session):
    return db.query(WebsiteTest).order_by(WebsiteTest.id.desc()).all()