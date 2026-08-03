import re


def analyze_security_issues(code: str):

    issues = []


    # SQL Injection

    sql_patterns = [
        "select * from",
        "insert into",
        "update",
        "delete from"
    ]


    for pattern in sql_patterns:

        if pattern in code.lower():

            issues.append(
                "Possible SQL Injection vulnerability"
            )

            break



    # Hardcoded Password

    if re.search(
        r"(password|passwd|pwd)\s*=\s*['\"].+['\"]",
        code,
        re.I
    ):

        issues.append(
            "Hardcoded password detected"
        )



    # API Key

    if re.search(
        r"(api[_-]?key|secret|token)\s*=\s*['\"].+['\"]",
        code,
        re.I
    ):

        issues.append(
            "Hardcoded API key or secret detected"
        )



    # XSS

    if (
        "innerHTML" in code
        or "dangerouslySetInnerHTML" in code
    ):

        issues.append(
            "Possible XSS vulnerability"
        )



    # Eval

    if "eval(" in code:

        issues.append(
            "Dangerous eval() usage detected"
        )



    # HTTP

    if "http://" in code:

        issues.append(
            "Insecure HTTP connection detected"
        )



    score = 100 - (len(issues) * 15)


    if score < 0:
        score = 0



    return {

        "tool": "Security Analyzer",

        "score": score,

        "issues": issues,

        "errors": ""

    }