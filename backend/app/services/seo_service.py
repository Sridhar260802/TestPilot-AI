import requests
from bs4 import BeautifulSoup

def seo_check(url: str):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title else None

        meta_description = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        meta_keywords = soup.find(
            "meta",
            attrs={"name": "keywords"}
        )

        canonical = soup.find(
            "link",
            attrs={"rel": "canonical"}
        )

        h1 = soup.find_all("h1")
        h2 = soup.find_all("h2")

        favicon = soup.find(
            "link",
            rel=lambda x: x and "icon" in x.lower()
        )

        og_title = soup.find(
            "meta",
            property="og:title"
        )

        score = 100

        if not title:
            score -= 20

        if not meta_description:
            score -= 20

        if len(h1) == 0:
            score -= 20

        if not canonical:
            score -= 10

        if not favicon:
            score -= 10

        if not og_title:
            score -= 10

        if score < 0:
            score = 0

        h1_count = len(h1)
        h2_count = len(h2)
        meta_description_content = meta_description.get("content") if meta_description else None
        meta_keywords_content = meta_keywords.get("content") if meta_keywords else None
        canonical_url = canonical.get("href") if canonical else None
        favicon_url = favicon.get("href") if favicon else None
        og_title_content = og_title.get("content") if og_title else None

        issues = []
        recommendations = []

        if not meta_keywords:
            issues.append("Meta keywords tag is missing.")
            recommendations.append("Add meta keywords for better search engine relevance.")

        if h1_count == 0:
            issues.append("No H1 heading found.")
            recommendations.append("Add exactly one H1 heading.")

        if h2_count == 0:
            issues.append("No H2 headings found.")
            recommendations.append("Use H2 headings to structure content.")

        if not canonical:
            issues.append("Canonical tag is missing.")
            recommendations.append("Add a canonical tag to prevent duplicate content.")

        if not favicon:
            issues.append("Favicon not found.")
            recommendations.append("Add a favicon for better branding.")

        return {
            "title": title,
            "meta_description": meta_description_content,
            "meta_keywords": meta_keywords_content,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "canonical": canonical_url,
            "favicon": favicon_url,
            "open_graph": og_title_content,
            "seo_score": score,
            "issues": issues,
            "recommendations": recommendations
        }
    except Exception as e:
        return {
            "seo_score": 0,
            "error": str(e)
        }