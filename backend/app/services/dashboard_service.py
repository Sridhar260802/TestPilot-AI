from sqlalchemy.orm import Session
from app.models.dashboard import DashboardStats


def get_dashboard_stats(db: Session):

    stats = db.query(DashboardStats).first()

    if not stats:
        stats = DashboardStats()

        db.add(stats)
        db.commit()
        db.refresh(stats)

    return stats
def update_dashboard_stats(db: Session, field: str, count: int = 1):

    stats = get_dashboard_stats(db)

    if hasattr(stats, field):
        current = getattr(stats, field)
        setattr(stats, field, current + count)

        db.commit()
        db.refresh(stats)

    return stats