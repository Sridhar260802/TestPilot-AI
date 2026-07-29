from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.models.dashboard import DashboardStats
from app.database.database import Base, engine
from app.database.dependency import get_db
from app.models.user import User
from app.core.security import hash_password
from app.routers.user import router as user_router
from app.routers.dasnboard import router as dashboard_router
from app.models.website_test import WebsiteTest
from app.routers.website_test import router as website_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TestPilot AI",
    version="1.0.0",
    description="AI Powered Software Testing Platform"
)

app.include_router(user_router)
app.include_router(dashboard_router)
app.include_router(website_router)


@app.get("/")
def root():
    return {"message": "TestPilot AI Backend Running Successfully"}


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    return {"status": "Database Connected Successfully"}


@app.get("/hash-test")
def hash_test():
    password = "Test@123"
    hashed = hash_password(password)
    return {
        "original": password,
        "hashed": hashed
    }