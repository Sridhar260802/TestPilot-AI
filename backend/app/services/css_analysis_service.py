import re


def analyze_css_code(code: str):

    issues = []

    # -----------------------
    # Font Family
    # -----------------------

    if "font-family" not in code:
        issues.append("Missing font-family")

    # -----------------------
    # Colors
    # -----------------------

    if (
        "color:" not in code
        and "background:" not in code
        and "background-color:" not in code
    ):
        issues.append("No colors defined")

    # -----------------------
    # !important
    # -----------------------

    important_count = code.count("!important")

    if important_count > 0:
        issues.append(
            f"{important_count} !important usages found"
        )

    # -----------------------
    # Empty CSS Rules
    # -----------------------

    empty_rules = re.findall(
        r"[^{]+\{\s*\}",
        code
    )

    if len(empty_rules) > 0:
        issues.append(
            f"{len(empty_rules)} empty CSS rules found"
        )

    # -----------------------
    # Duplicate Selectors
    # -----------------------

    selectors = re.findall(
        r"([^{]+)\{",
        code
    )

    cleaned = []

    for s in selectors:
        cleaned.append(s.strip())

    duplicate = len(cleaned) - len(set(cleaned))

    if duplicate > 0:
        issues.append(
            f"{duplicate} duplicate selectors found"
        )

    # -----------------------
    # Inline Styles
    # -----------------------

    if "style=" in code:
        issues.append(
            "Inline styles detected"
        )

    # -----------------------
    # Score
    # -----------------------

    score = 100

    score -= len(issues) * 10

    if score < 0:
        score = 0

    return {

        "tool": "CSS Analyzer",

        "score": score,

        "issues": issues,

        "important_usage": important_count,

        "duplicate_selectors": duplicate,

        "empty_rules": len(empty_rules)

    }