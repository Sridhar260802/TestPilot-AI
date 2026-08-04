from sqlalchemy.orm import Session
from app.models.code_analysis import CodeAnalysis


def get_all_reports(db: Session):

    return (
        db.query(CodeAnalysis)
        .order_by(CodeAnalysis.created_at.desc())
        .all()
    )


def get_report_by_id(db: Session, report_id: int):

    return (
        db.query(CodeAnalysis)
        .filter(CodeAnalysis.id == report_id)
        .first()
    )


def delete_report(db: Session, report_id: int):

    report = (
        db.query(CodeAnalysis)
        .filter(CodeAnalysis.id == report_id)
        .first()
    )

    if report is None:
         return False
    print("Deleting report with ID:", report_id)
    report = (db.query(CodeAnalysis).filter(CodeAnalysis.id == report_id).first())
    print("Report found:", report)

    db.delete(report)
    db.commit()

    return True