from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.models.dashboard import DashboardStats
from app.database.database import Base, engine
from app.database.dependency import get_db
from app.models.user import User
from app.core.security import hash_password

from app.routers.user import router as user_router
from app.routers.dashboard import router as dashboard_router
from app.models.website_test import WebsiteTest, FunctionalTestResult
from app.models.security_audit import SecurityAudit
from app.models.payment import PaymentTransaction
from app.models.mobile_test import MobileAppTest
from app.routers.website_test import router as website_router
from app.routers.code_analysis import router as code_router
from app.routers.pdf_report import router as pdf_router
from app.routers.security_audit import router as security_audit_router
from app.routers.plans import router as plans_router
from app.routers.payments import router as payments_router
from app.routers.mobile_test import router as mobile_router


# --------------------------------------------------
# CREATE APP - ONLY ONCE
# --------------------------------------------------

app = FastAPI(
    title="Crosbytech",
    version="1.0.0",
    description="AI Powered Software Testing Platform",
    swagger_ui_parameters={
        "persistAuthorization": True
    }
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


def _ensure_website_tests_history_columns():
    """
    create_all() only creates tables that don't exist yet — it never alters
    an existing one. On a DB created before user_id/plan/created_at were
    added to WebsiteTest, add them here so per-user history keeps working
    without needing to delete the old testpilot.db.
    """
    with engine.connect() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(website_tests)")}
        if "user_id" not in existing:
            conn.exec_driver_sql("ALTER TABLE website_tests ADD COLUMN user_id INTEGER")
        if "plan" not in existing:
            conn.exec_driver_sql("ALTER TABLE website_tests ADD COLUMN plan VARCHAR")
        if "created_at" not in existing:
            conn.exec_driver_sql("ALTER TABLE website_tests ADD COLUMN created_at DATETIME")
        conn.commit()


_ensure_website_tests_history_columns()


def _ensure_dashboard_stats_mobile_column():
    """Same reasoning as above: create_all() won't add mobile_tests to an
    already-existing dashboard_stats table."""
    with engine.connect() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(dashboard_stats)")}
        if "mobile_tests" not in existing:
            conn.exec_driver_sql("ALTER TABLE dashboard_stats ADD COLUMN mobile_tests INTEGER DEFAULT 0")
        conn.commit()


_ensure_dashboard_stats_mobile_column()


# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(user_router)
app.include_router(dashboard_router)
app.include_router(website_router)
app.include_router(code_router)
app.include_router(pdf_router)
app.include_router(security_audit_router)
app.include_router(plans_router)
app.include_router(payments_router)
app.include_router(mobile_router)


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Crosbytech Backend Running Successfully"
    }


# --------------------------------------------------
# DATABASE TEST
# --------------------------------------------------

@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    return {
        "status": "Database Connected Successfully"
    }


# --------------------------------------------------
# HASH TEST
# --------------------------------------------------

@app.get("/hash-test")
def hash_test():
    password = "Test@123"
    hashed = hash_password(password)

    return {
        "original": password,
        "hashed": hashed
    }


# --------------------------------------------------
# FRONTEND CONNECTION TEST
# --------------------------------------------------

@app.get("/api/test")
def test_api():
    return {
        "message": "Backend connected successfully!"
    }