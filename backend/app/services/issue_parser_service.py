def analyze_issue_severity(ai_response: str):

    text = ai_response.lower()

    critical = 0
    high = 0
    medium = 0
    low = 0


    critical_keywords = [
        "data leak",
        "api key exposed",
        "critical vulnerability",
        "sql injection"
    ]

    high_keywords = [
        "security issue",
        "major bug",
        "authentication issue"
    ]

    medium_keywords = [
        "performance",
        "validation",
        "optimization"
    ]

    low_keywords = [
        "formatting",
        "documentation",
        "style"
    ]


    for word in critical_keywords:
        if word in text:
            critical += 1

    for word in high_keywords:
        if word in text:
            high += 1

    for word in medium_keywords:
        if word in text:
            medium += 1

    for word in low_keywords:
        if word in text:
            low += 1


    return {
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low
    }