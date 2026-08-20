from datetime import datetime
from typing import Optional
from pydantic import BaseModel, model_validator


class MobileTestHistoryItem(BaseModel):
    id: int
    platform: str
    file_name: str
    package_or_bundle_id: Optional[str] = None
    app_version: Optional[str] = None
    plan: Optional[str] = None
    scan_depth: Optional[str] = None
    security_score: int
    severity: str
    issue_count: int
    created_at: Optional[datetime] = None
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
        try:
            obj.report_available = bool(report_path)
        except Exception:
            pass
        return obj