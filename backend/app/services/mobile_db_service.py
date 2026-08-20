import json
from sqlalchemy.orm import Session
from app.models.mobile_test import MobileAppTest


def save_mobile_test(
    db: Session,
    platform: str,
    file_name: str,
    analysis: dict,
    user_id: int = None,
    plan: str = None,
    report_path: str = None,
) -> MobileAppTest:
    overview = analysis.get("overview", {})
    package_or_bundle_id = overview.get("package") or overview.get("bundle_id")
    app_version = overview.get("version_name") or overview.get("version")

    obj = MobileAppTest(
        user_id=user_id,
        plan=plan,
        scan_depth=analysis.get("scan_depth"),
        platform=platform,
        file_name=file_name,
        package_or_bundle_id=package_or_bundle_id,
        app_version=app_version,
        security_score=analysis.get("security_score", 0),
        severity=analysis.get("severity", "Low"),
        issue_count=len(analysis.get("issues", [])),
        result_json=json.dumps(analysis),
        report_path=report_path,
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_user_mobile_tests(db: Session, user_id: int, limit: int = 20):
    return (
        db.query(MobileAppTest)
        .filter(MobileAppTest.user_id == user_id)
        .order_by(MobileAppTest.id.desc())
        .limit(limit)
        .all()
    )


def get_user_mobile_test_by_id(db: Session, test_id: int, user_id: int):
    return (
        db.query(MobileAppTest)
        .filter(MobileAppTest.id == test_id, MobileAppTest.user_id == user_id)
        .first()
    )