from pydantic import BaseModel

class DashboardResponse(BaseModel):
    total_tests: int
    website_tests: int
    code_analysis: int
    ai_suggestions: int
    reports_generated: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int

    class Config:
        from_attributes = True