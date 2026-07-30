from turtle import update

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

from app.services.performance_service import performance_check
from app.services.groq_service import generate_ai_suggestions
from fastapi.responses import FileResponse
from app.services.dashboard_service import update_dashboard_stats
from app.services.pdf_service import generate_pdf_report
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
    update_dashboard_stats(
        db,"website_tests"
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
    seo = seo_check(data.url)
    accessibility = accessibility_check(data.url)
    performance = performance_check(data.url)

    prompt = f"""
    Website URL: {data.url}

    Website Health Score: {website.get("health_score", 0)}
    Broken Links: {broken.get("broken_links", 0)}
    SEO Score: {seo.get("seo_score", 0)}
    Accessibility Score: {accessibility.get("accessibility_score", 0)}
    Performance Score: {performance.get("performance_score", 0)}

    Analyze this website and provide:
    1. Overall website health.
    2. SEO improvements.
    3. Accessibility improvements.
    4. Performance improvements.
    5. Priority-wise recommendations.
    """

    return {
        "website": website,
        "broken_links": broken,
        "seo": seo,
        "accessibility": accessibility,
        "performance": performance,
        "ai_suggestions": generate_ai_suggestions(prompt)
    }
    
    
@router.post("/report")
def report(data: WebsiteTestRequest,
           db: Session = Depends(get_db)):

    website = test_website(data.url)
    seo = seo_check(data.url)
    accessibility = accessibility_check(data.url)
    performance = performance_check(data.url)

    report_data = {
        "Website": data.url,
        "Health Score": website.get("health_score", 0),
        "SEO Score": seo.get("seo_score", 0),
        "Accessibility Score": accessibility.get("accessibility_score", 0),
        "Performance Score": performance.get("performance_score", 0),
    }

    pdf = generate_pdf_report(report_data)
    update_dashboard_stats(db,"reports_generated")
    return FileResponse(
        pdf,
        media_type="application/pdf",
        filename="Website_Report.pdf"
    )   