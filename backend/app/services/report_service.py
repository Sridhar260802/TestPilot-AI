from sqlalchemy.orm import Session
from app.models.code_analysis import CodeAnalysis


def get_latest_report(db: Session):

    return (
        db.query(CodeAnalysis)
        .order_by(CodeAnalysis.id.desc())
        .first()
    )