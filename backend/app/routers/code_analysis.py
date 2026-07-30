from fastapi import APIRouter
from app.schemas.code_analysis import CodeRequest
from app.services.groq_service import generate_ai_suggestions
from app.services.code_analysis_service import (analyze_python_code,analyze_javascript_code)
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database.dependency import get_db
from app.services.dashboard_service import update_dashboard_stats
from app.services.issue_parser_service import analyze_issue_severity


router = APIRouter(
    prefix="/code",
    tags=["Code Analysis"]
)

@router.post("/python")
def analyze(data: CodeRequest,db:Session = Depends(get_db)):

    pylint_result = analyze_python_code(data.code)

    prompt = f"""
You are a Senior Software Engineer.

Analyze this Pylint report and provide:

1. Overall Code Quality Score out of 100
2. Issues found
3. Best Practices
4. Optimizations
5. Security Suggestions
6. Clean corrected version recommendation

Pylint Report:

{pylint_result["report"]}
"""

    ai_response = generate_ai_suggestions(prompt)
    severity = analyze_issue_severity(ai_response)

    update_dashboard_stats(
        db,
        "critical_issues",
        severity["critical"]
    )

    update_dashboard_stats(
        db,
        "high_issues",
        severity["high"]
    ) 

    update_dashboard_stats(
        db,
        "medium_issues",
        severity["medium"]
    )

    update_dashboard_stats(
        db,
        "low_issues",
        severity["low"]
    )
    update_dashboard_stats(db,"code_analysis")
    update_dashboard_stats(db,"ai_suggestions")

    return {
        "tool": "Pylint",
        "pylint_report": pylint_result["report"],
        "ai_suggestions": ai_response
    }   
        
@router.post("/javascript")
def analyze_javascript(
    data: CodeRequest,
    db: Session = Depends(get_db)
):

    eslint_result = analyze_javascript_code(data.code)

    prompt = f"""
    You are a Senior JavaScript Code Reviewer.

    Analyze this ESLint report and provide:

    1. Overall Code Quality Score out of 100
    2. Errors found
    3. Improvements
    4. Best Practices
    5. Security Suggestions
    6. Corrected Code

    Return ONLY in this format:

    ⭐ Code Score: xx/100

    🔴 Errors:
    - ...

    🟡 Improvements:
    - ...

    🟢 Best Practices:
    - ...

    🔒 Security:
    - ...

    📝 Corrected Code:
    ```javascript
    ...
    """
    ai_response = generate_ai_suggestions(prompt)
    severity = analyze_issue_severity(ai_response)
    
    update_dashboard_stats(
        db,
        "critical_issues",
        severity["critical"]
    )

    update_dashboard_stats(
        db,
        "high_issues",
        severity["high"]
    )

    update_dashboard_stats(
        db,
        "medium_issues",
        severity["medium"]
    )

    update_dashboard_stats(
        db,
        "low_issues",
        severity["low"]
    )

    # 👇 ITHA inga add pannanum
    update_dashboard_stats(
        db,
        "code_analysis"
    )
    update_dashboard_stats(
        db,"ai_suggestions"
    )

    return {
        "tool": "ESLint",
        "eslint_report": eslint_result["report"],
        "ai_suggestions": ai_response
    }