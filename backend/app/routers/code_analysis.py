from fastapi import APIRouter
from app.schemas.code_analysis import CodeRequest
from app.services.groq_service import generate_ai_suggestions
from app.services.code_analysis_service import (analyze_python_code,analyze_javascript_code)
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database.dependency import get_db
from app.services.dashboard_service import update_dashboard_stats
from app.services.issue_parser_service import analyze_issue_severity
from app.services.html_analysis_service import analyze_html_code
from app.services.css_analysis_service import analyze_css_code
from app.services.react_analysis_service import analyze_react_code
from app.services.java_analysis_service import analyze_java_code
from fastapi import UploadFile, File
from app.services.file_reader_service import read_code_file
from app.services.code_router_service import analyze_code_by_extension
from app.services.ai_analysis_service import generate_code_ai_review
from app.services.severity_service import analyze_issue_severity
from app.services.code_analysis_db_service import (save_code_analysis,get_code_analysis_history)
from app.services.security_analysis_service import analyze_security_issues




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
@router.post("/html")
def analyze_html(
    data: CodeRequest,
    db: Session = Depends(get_db)
):

    html_result = analyze_html_code(data.code)

    prompt = f"""
    You are a Senior HTML Code Reviewer.

    Analyze this HTML report and provide:

    1. Overall HTML Quality Score out of 100
    2. Issues found
    3. SEO Improvements
    4. Accessibility Improvements
    5. Best Practices
    6. Corrected HTML Code

    HTML Report:

    Score: {html_result["score"]}

    Issues:
    {html_result["issues"]}
    """

    ai_response = generate_ai_suggestions(prompt)

    severity = analyze_issue_severity(ai_response)

    update_dashboard_stats(db, "critical_issues", severity["critical"])
    update_dashboard_stats(db, "high_issues", severity["high"])
    update_dashboard_stats(db, "medium_issues", severity["medium"])
    update_dashboard_stats(db, "low_issues", severity["low"])

    update_dashboard_stats(db, "code_analysis")
    update_dashboard_stats(db, "ai_suggestions")

    return {
        "tool": "HTML Analyzer",
        "html_report": html_result,
        "ai_suggestions": ai_response
    }  
@router.post("/css")
def analyze_css(
    data: CodeRequest,
    db: Session = Depends(get_db)
):

    css_result = analyze_css_code(data.code)

    prompt = f"""
    You are a Senior CSS Code Reviewer.

    Analyze this CSS report and provide:

    1. Overall CSS Quality Score out of 100
    2. Issues found
    3. Best Practices
    4. Performance Improvements
    5. Maintainability Suggestions
    6. Corrected CSS Code

    CSS Report:

    Score: {css_result["score"]}

    Issues:
    {css_result["issues"]}
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

    update_dashboard_stats(
        db,
        "code_analysis"
    )

    update_dashboard_stats(
        db,
        "ai_suggestions"
    )

    return {
        "tool": "CSS Analyzer",
        "css_report": css_result,
        "ai_suggestions": ai_response
    }      
@router.post("/react")
def analyze_react(
    data: CodeRequest,
    db: Session = Depends(get_db)
):

    react_result = analyze_react_code(data.code)

    prompt = f"""
    You are a Senior React Code Reviewer.

    Analyze this React report and provide:

    1. Overall React Code Quality Score out of 100
    2. Issues found
    3. Best Practices
    4. Performance Improvements
    5. React Recommendations
    6. Corrected React Code

    React Report:

    Score: {react_result["score"]}

    Issues:
    {react_result["issues"]}
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

    update_dashboard_stats(
        db,
        "code_analysis"
    )

    update_dashboard_stats(
        db,
        "ai_suggestions"
    )

    return {
        "tool": "React Analyzer",
        "react_report": react_result,
        "ai_suggestions": ai_response
    } 
@router.post("/java")
def analyze_java(
    data: CodeRequest,
    db: Session = Depends(get_db)
):

    java_result = analyze_java_code(data.code)

    prompt = f"""
    You are a Senior Java Code Reviewer.

    Analyze this Java report and provide:

    1. Overall Java Code Quality Score out of 100
    2. Issues found
    3. Best Practices
    4. Performance Improvements
    5. Security Suggestions
    6. Corrected Java Code

    Java Report:

    Score: {java_result["score"]}

    Issues:
    {java_result["issues"]}
    """

    ai_response = generate_ai_suggestions(prompt)

    severity = analyze_issue_severity(ai_response)

    update_dashboard_stats(db, "critical_issues", severity["critical"])
    update_dashboard_stats(db, "high_issues", severity["high"])
    update_dashboard_stats(db, "medium_issues", severity["medium"])
    update_dashboard_stats(db, "low_issues", severity["low"])

    update_dashboard_stats(db, "code_analysis")
    update_dashboard_stats(db, "ai_suggestions")

    return {
        "tool": "Java Analyzer",
        "java_report": java_result,
        "ai_suggestions": ai_response
    }    
    
@router.post("/upload")
def upload_code(
    file: UploadFile = File(...)
):

    result = read_code_file(file)

    return result    

@router.post("/analyze-file")
def analyze_uploaded_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    file_data = read_code_file(file)

    if "error" in file_data:
        return file_data


    result = analyze_code_by_extension(
        file_data["extension"],
        file_data["code"]
    )
    security_results = analyze_security_issues(
        file_data["code"])


    ai_review = generate_code_ai_review(
        file_data["filename"],
        file_data["extension"],
        {
            "code_analysis": result,
            "security_analysis": security_results
        }
    )


    severity = analyze_issue_severity(
        ai_review
    )


    save_code_analysis(
        db=db,
        filename=file_data["filename"],
        language=file_data["extension"],
        analysis=result,
        severity=severity,
        ai=ai_review
    )


    return {

        "filename": file_data["filename"],

        "language": file_data["extension"],

        "analysis": result,
        
        "security_analysis": security_results,

        "severity": severity,

        "ai_suggestions": ai_review

    }
@router.get("/history")
def code_history(
    db: Session = Depends(get_db)
):

    return get_code_analysis_history(db)    