from app.services.groq_service import generate_ai_suggestions


def generate_code_ai_review(
    filename,
    language,
    analysis
):

    code = analysis.get("code_analysis", {})
    security = analysis.get("security_analysis", {})

    prompt = f"""
You are a Senior Software Code Reviewer.

Analyze the following Static Code Analysis Report.

File Name:
{filename}

Language:
{language}

=========================
CODE ANALYSIS
=========================

Code Score:
{code.get("score", 0)}

Code Issues:
{code.get("issues", [])}

Analyzer Errors:
{code.get("errors", "")}

=========================
SECURITY ANALYSIS
=========================

Security Score:
{security.get("score", 0)}

Security Issues:
{security.get("issues", [])}

Security Errors:
{security.get("errors", "")}

=========================

Generate a professional review in VALID JSON format only.

Return exactly these fields:

{{
  "Overall Code Quality": "",
  "Critical Issues": "",
  "Security Risks": "",
  "Performance Improvements": "",
  "Best Practices": "",
  "Priority-wise Recommendations": [
    ""
  ],
  "Developer Action Items": [
    ""
  ]
}}

Use ONLY the analyzer results above.
Do not return "Unknown" if scores or issues are available.
Do not invent issues.
"""

    return generate_ai_suggestions(prompt)