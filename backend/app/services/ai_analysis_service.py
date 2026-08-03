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