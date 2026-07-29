from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.seo_service import seo_check
from app.database.dependency import get_db
from app.schemas.website_test import WebsiteTestRequest
from app.services.accessibility_service import accessibility_check
from app.services.website_service import (
    test_website,
    check_broken_links,
)
from app.services.website_service import (
    test_website,
    check_broken_links,
    check_seo,
    check_accessibility,
    check_performance,
)
from app.services.performance_service import performance_check
from app.services.groq_service import generate_ai_suggestions

from app.services.website_db_service import (
    save_website_test,
    get_all_website_tests,
)

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
        db=db,
        url=data.url,
        result=result
    )

    return result


@router.get("/history")
def website_history(
    db: Session = Depends(get_db)
):
    return get_all_website_tests(db)


@router.post("/check-links")
def broken_links(
    data: WebsiteTestRequest
):
    return check_broken_links(data.url)


@router.post("/seo")
def seo_test(data:WebsiteTestRequest):
    return seo_check(data.url)


@router.post("/accessibility")
def accessibility_test(data:WebsiteTestRequest):
    return accessibility_check(data.url)   


@router.post("/performance")
def performance_test(data:WebsiteTestRequest):
    return performance_check(data.url)

@router.post("/ai-test")
def ai_test(data: WebsiteTestRequest):

    website = test_website(data.url)
    broken = check_broken_links(data.url)
    seo = check_seo(data.url)
    accessibility = check_accessibility(data.url)
    performance = check_performance(data.url)

    prompt = f"""
    Website URL: {data.url}

    Website Health: {website["health_score"]}
    Broken Links: {broken["broken_links"]}
    SEO Score: {seo["seo_score"]}
    Accessibility Score: {accessibility["accessibility_score"]}
    Performance Score: {performance["performance_score"]}

    Analyze ONLY this website and give personalized suggestions.
    """

    return {
        "response": generate_ai_suggestions(prompt)
    }