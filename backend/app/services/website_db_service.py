from sqlalchemy.orm import Session
from app.models.website_test import WebsiteTest, FunctionalTestResult
import json


def save_website_test(
    db: Session,
    url: str,
    website: dict,
    seo: dict,
    accessibility: dict,
    performance: dict,
    security: dict,
    broken: dict,
    ai: dict,
    severity: str
):

    obj = WebsiteTest(

        url=url,

        status_code=website.get("status_code", 0),

        response_time=website.get("response_time", 0),

        ssl_status=website.get("ssl_status", "Unknown"),

        test_status=website.get("test_status", "Unknown"),

        health_score=website.get("health_score", 0),

        seo_score=seo.get("seo_score", 0),

        accessibility_score=accessibility.get("accessibility_score", 0),

        performance_score=performance.get("performance_score", 0),

        security_score=security.get("security_score", 0),

        broken_links=broken.get("broken_links", 0),

        ai_suggestions=json.dumps(ai),

        severity=severity

    )

    db.add(obj)

    db.commit()

    db.refresh(obj)

    return obj


def get_all_website_tests(db: Session):

    return (

        db.query(WebsiteTest)

        .order_by(WebsiteTest.id.desc())

        .all()

    )


def save_functional_test_result(
    db: Session,
    url: str,
    functional: dict
):

    obj = FunctionalTestResult(

        url=url,

        functional_score=functional.get("functional_score", 0),

        total_modules=functional.get("total_modules", 0),

        executed_modules=functional.get("executed_modules", 0),

        tested_modules=functional.get(
            "tested_modules",
            functional.get("passed", 0) + functional.get("failed", 0)
        ),

        passed=functional.get("passed", 0),

        failed=functional.get("failed", 0),

        partial=functional.get("partial", 0),

        skipped=functional.get("skipped", 0),

        not_available=functional.get("not_available", 0),

        results_json=json.dumps(functional.get("results", []))

    )

    db.add(obj)

    db.commit()

    db.refresh(obj)

    return obj


def get_all_functional_test_results(db: Session):

    return (

        db.query(FunctionalTestResult)

        .order_by(FunctionalTestResult.id.desc())

        .all()

    )