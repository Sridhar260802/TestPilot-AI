from datetime import datetime
from typing import Optional
from pydantic import BaseModel, model_validator

class WebsiteTestRequest(BaseModel):
    url: str


class WebsiteTestHistoryItem(BaseModel):
    id: int
    url: str
    plan: Optional[str] = None
    health_score: int
    severity: str
    created_at: Optional[datetime] = None
    # Whether GET /history/{id}/download will actually return a PDF.
    # Derived from the ORM row's report_path — the raw filesystem path
    # itself is never sent to the frontend.
    report_available: bool = False

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def _derive_report_available(cls, obj):
        report_path = getattr(obj, "report_path", None)
        if isinstance(obj, dict):
            report_path = obj.get("report_path")
            obj = dict(obj)
            obj["report_available"] = bool(report_path)
            return obj

        # ORM object: attach the derived attribute so from_attributes
        # picks it up like a normal column.
        try:
            obj.report_available = bool(report_path)
        except Exception:
            pass
        return obj


class WebsiteTestResponse(BaseModel):
    id: int
    url: str
    status_code: int
    response_time: float
    ssl_status: str
    test_status: str

    class Config:
        from_attributes = True