from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependency import get_db
from app.models.security_audit import SecurityAudit


router = APIRouter(
    prefix="/security-audit",
    tags=["Security Audit"]
)


@router.post("/save")
def save_security_audit(
    data: dict,
    db: Session = Depends(get_db)
):
    audit = SecurityAudit(
        url=data.get("url"),
        status=data.get("status", "FAIL"),
        security_score=data.get("security_score", 0),
        issue=data.get("issue"),
        possible_reason=data.get("possible_reason"),
        recommendation=data.get("recommendation"),
        developer_action=data.get("developer_action")
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "status": "success",
        "message": "Security audit saved successfully",
        "audit_id": audit.id
    }


@router.get("/")
def get_security_audits(
    db: Session = Depends(get_db)
):
    audits = (
        db.query(SecurityAudit)
        .order_by(SecurityAudit.id.desc())
        .all()
    )

    return audits