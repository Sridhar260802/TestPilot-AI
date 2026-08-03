import re


def analyze_issue_severity(text: str):

    critical = 0
    high = 0
    medium = 0
    low = 0


    text = text.lower()


    critical_words = [
        "security vulnerability",
        "data breach",
        "sql injection",
        "remote code execution",
        "critical"
    ]


    high_words = [
        "performance issue",
        "memory leak",
        "authentication",
        "unsafe",
        "high"
    ]


    medium_words = [
        "optimization",
        "maintainability",
        "warning",
        "medium"
    ]


    low_words = [
        "suggestion",
        "style",
        "formatting",
        "low"
    ]


    for word in critical_words:
        if word in text:
            critical += 1


    for word in high_words:
        if word in text:
            high += 1


    for word in medium_words:
        if word in text:
            medium += 1


    for word in low_words:
        if word in text:
            low += 1


    return {

        "critical": critical,

        "high": high,

        "medium": medium,

        "low": low

    }