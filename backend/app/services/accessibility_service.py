import requests
from bs4 import BeautifulSoup


def accessibility_check(url: str):
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    images = soup.find_all("img")
    buttons = soup.find_all("button")
    forms = soup.find_all("form")

    images_without_alt = sum(
        1 for img in images if not img.get("alt")
    )

    buttons_without_text = sum(
        1 for btn in buttons if not btn.text.strip()
    )

    score = 100

    score -= images_without_alt * 5
    score -= buttons_without_text * 10

    if score < 0:
        score = 0

    return {
        "total_images": len(images),
        "images_without_alt": images_without_alt,
        "buttons": len(buttons),
        "buttons_without_text": buttons_without_text,
        "forms": len(forms),
        "accessibility_score": score
    }