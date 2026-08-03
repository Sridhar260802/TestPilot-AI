from bs4 import BeautifulSoup


def analyze_html_code(code: str):

    soup = BeautifulSoup(
        code,
        "html.parser"
    )

    issues = []


    if not soup.title:
        issues.append(
            "Missing <title> tag"
        )


    meta = soup.find(
        "meta",
        attrs={
            "name":"description"
        }
    )

    if not meta:
        issues.append(
            "Missing Meta Description"
        )


    html = soup.find("html")

    if not html or not html.get("lang"):
        issues.append(
            "Missing html lang attribute"
        )


    if len(soup.find_all("h1")) == 0:
        issues.append(
            "Missing H1 tag"
        )


    images = soup.find_all("img")

    missing_alt = 0

    for img in images:

        if not img.get("alt"):
            missing_alt += 1


    if missing_alt > 0:
        issues.append(
            f"{missing_alt} images missing alt attribute"
        )


    forms = soup.find_all("form")

    labels = soup.find_all("label")

    if len(forms) > 0 and len(labels) == 0:
        issues.append(
            "Forms found but labels missing"
        )


    score = 100 - (len(issues) * 10)

    if score < 0:
        score = 0


    return {

        "tool": "HTML Analyzer",

        "score": score,

        "issues": issues,

        "errors": ""

    }