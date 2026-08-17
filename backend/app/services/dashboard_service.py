from sqlalchemy.orm import Session
from app.models.dashboard import DashboardStats


def get_dashboard_stats(db: Session, user_id: int = None):
    """
    Returns the stats row for a single user (user_id given) or the shared
    row used by not-logged-in endpoints (user_id=None). Each user gets
    their own row so one person's counts never show up on another
    person's dashboard.
    """
    stats = db.query(DashboardStats).filter(
        DashboardStats.user_id == user_id
    ).first()

    if not stats:
        stats = DashboardStats(user_id=user_id)

        db.add(stats)
        db.commit()
        db.refresh(stats)

    return stats


def update_dashboard_stats(db: Session, field: str, count: int = 1, user_id: int = None):
    stats = get_dashboard_stats(db, user_id)

    if hasattr(stats, field):
        current = getattr(stats, field)
        setattr(stats, field, current + count)

        db.commit()
        db.refresh(stats)

    return stats