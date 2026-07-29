from fastapi import APIRouter
from app.schemas.website_test import WebsiteTestRequest
from app.services.website_service import test_website
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database.dependency import get_db
from app.services.website_db_service import save_website_test
from app.services.website_db_service import (save_website_test,get_all_website_tests)
router = APIRouter(
    prefix="/website",
    tags=["Website Testing"]
)

@router.post("/test")
def website_test(
    data: WebsiteTestRequest,
    db: Session = Depends(get_db)
):
    result = test_website(data.url)

    save_website_test(
        db,
        data.url,
        result
    )

    return result

@router.get("/history")
def website_history(db: Session = Depends(get_db)):
    return get_all_website_tests(db)