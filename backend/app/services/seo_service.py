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

        return {
            "title": title,
            "meta_description": bool(meta_description),
            "meta_keywords": bool(meta_keywords),
            "h1_count": len(h1),
            "h2_count": len(h2),
            "canonical": bool(canonical),
            "favicon": bool(favicon),
            "open_graph": bool(og_title),
            "seo_score": score
        }

    except Exception as e:
        return {
            "seo_score": 0,
            "error": str(e)
        }