from sqlalchemy.orm import Session
from app.models.website_test import WebsiteTest, FunctionalTestResult
import json


def _safe_broken_links_count(broken):
    """
    broken_links must always be an int for the DB column.
    Upstream (check_broken_links / other callers) can hand us:
      - a dict like {"broken_links": 3, ...}
      - a plain int
      - a list of broken link URLs (legacy/alternate shape)
    Normalize all of these to an int count so SQLAlchemy never
    chokes with 'Error binding parameter: type list is not supported'.
    """
    if isinstance(broken, dict):
        value = broken.get("broken_links", 0)
    else:
        value = broken

    if isinstance(value, list):
        return len(value)

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


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
    severity: str,
    user_id: int = None,
    plan: str = None,
    report_path: str = None,
):

    obj = WebsiteTest(

        user_id=user_id,

        plan=plan,

        report_path=report_path,

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

        broken_links=_safe_broken_links_count(broken),

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


def get_user_website_tests(db: Session, user_id: int, limit: int = 20):
    """All websites this user has tested, most recent first — powers the
    'recent audits' history on the dashboard."""

    return (
        db.query(WebsiteTest)
        .filter(WebsiteTest.user_id == user_id)
        .order_by(WebsiteTest.id.desc())
        .limit(limit)
        .all()
    )


def get_user_website_test_by_id(db: Session, test_id: int, user_id: int):
    """A single history row, but ONLY if it belongs to this user — used
    by the report-download endpoint so one user can't pull another
    user's report by guessing/incrementing the id."""

    return (
        db.query(WebsiteTest)
        .filter(WebsiteTest.id == test_id, WebsiteTest.user_id == user_id)
        .first()
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