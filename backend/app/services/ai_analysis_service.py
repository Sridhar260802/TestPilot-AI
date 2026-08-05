from app.services.groq_service import generate_ai_suggestions


def generate_code_ai_review(
    filename,
    language,
    analysis
):

    prompt = f"""

You are a Senior Software Code Reviewer.

Analyze this code analysis report.

File Name:
{filename}

Language:
{language}

Analyzer Result:

Score:
{analysis.get("score",0)}

Issues:
{analysis.get("issues",[])}
Errors:
{analysis.get("errors","")}


Provide:

1. Overall Code Quality
2. Critical Issues
3. Security Risks
4. Performance Improvements
5. Best Practices
6. Priority-wise Recommendations
7. Developer Action Items


Give response in clear JSON format.

"""


    ai_response = generate_ai_suggestions(
        prompt
    )


    return ai_response


def generate_website_ai_review(
    url,
    health_score,
    broken_links,
    seo,
    accessibility,
    performance,
    security
):

    prompt = f"""
You are a Senior Website Auditor.

Website URL:
{url}

Health Score:
{health_score}

Broken Links:
{broken_links.get("broken_links",0)}

SEO Score:
{seo.get("seo_score",0)}
SEO Issues:
{seo.get("issues",[])}

Accessibility Score:
{accessibility.get("accessibility_score",0)}

Accessibility Issues:
{accessibility.get("issues",[])}

Accessibility Recommendations:
{accessibility.get("recommendations",[])}

Performance Score:
{performance.get("performance_score",0)}
Performance Issues:
{performance.get("issues",[])}

Security Score:
{security.get("security_score",0)}
Security Issues:
{security.get("issues",[])}

Return JSON only.

{{
    "Overall Website Health":"",
    "Critical Issues":[],
    "SEO Improvements":[],
    "Accessibility Improvements":[],
    "Performance Improvements":[],
    "Security Improvements":[],
    "Priority Recommendations":[],
    "Developer Action Items":[]
}}
"""

    return generate_ai_suggestions(prompt)