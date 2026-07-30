from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.dashboard_service import update_dashboard_stats
from app.database.dependency import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard_stats


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats", response_model=DashboardResponse)
def dashboard_stats(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)

@router.post("/increment/{field}")
def increment_dashboard(field: str, db: Session = Depends(get_db)):
    return update_dashboard_stats(db, field)