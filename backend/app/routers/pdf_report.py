import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.dependency import get_db
from app.services.report_service import get_latest_report
from app.services.pdf_service import generate_code_pdf
from app.services.report_history_service import(get_all_reports, get_report_by_id, delete_report)

router = APIRouter(
    prefix="/report",
    tags=["PDF Report"]
)


@router.get("/latest")
def download_latest_report(
    db: Session = Depends(get_db)
):

    latest = get_latest_report(db)

    if not latest:
        raise HTTPException(
            status_code=404,
            detail="No code analysis report found."
        )

    data = {
        "filename": latest.filename,
        "language": latest.language,

        "analysis": json.loads(latest.analysis_json),

        "security_analysis": json.loads(latest.security_json),

        "severity": json.loads(latest.severity),

        "ai_suggestions": latest.ai_suggestions
    }

    pdf_file = generate_code_pdf(data)

    return FileResponse(
        path=pdf_file,
        filename="code_analysis_report.pdf",
        media_type="application/pdf"
    )
@router.get("/history")
def report_history(
    db: Session = Depends(get_db)
):
    return get_all_reports(db)


@router.get("/{report_id}")
def report_details(
    report_id: int,
    db: Session = Depends(get_db)
):

    report = get_report_by_id(
        db,
        report_id
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return report


@router.delete("/{report_id}")
def remove_report(
    report_id: int,
    db: Session = Depends(get_db)
):

    result = delete_report(
        db,
        report_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return {
        "message": "Report deleted successfully"
    } 
    