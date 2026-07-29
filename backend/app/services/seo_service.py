import requests
from bs4 import BeautifulSoup


def seo_check(url: str):
    response = requests.get(url, timeout=10)

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string.strip() if soup.title else "No Title"

    meta_description = (
        soup.find("meta", attrs={"name": "description"}) is not None
    )

    h1_tags = len(soup.find_all("h1"))

    images = soup.find_all("img")

    images_without_alt = sum(
        1 for img in images if not img.get("alt")
    )

    score = 100

    if not meta_description:
        score -= 20

    if h1_tags == 0:
        score -= 20

    score -= images_without_alt * 5

    if score < 0:
        score = 0

    return {
        "title": title,
        "meta_description": meta_description,
        "h1_tags": h1_tags,
        "images_without_alt": images_without_alt,
        "seo_score": score
    }