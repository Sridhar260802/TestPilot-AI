import time
import requests
from bs4 import BeautifulSoup
from app.services.seo_service import seo_check
from app.services.accessibility_service import accessibility_check
from app.services.performance_service import performance_check

def test_website(url: str):
    start = time.time()

    try:
        response = requests.get(url, timeout=10)

        end = time.time()

        seo = seo_check(url)
        accessibility = accessibility_check(url)
        performance = performance_check(url)

        health_score = int(
            (
                seo["seo_score"] +
                accessibility["accessibility_score"] +
                performance["performance_score"]
            ) / 3
        )

        return {
            "status_code": response.status_code,
            "response_time": round(end - start, 2),
            "ssl_status": "Valid" if url.startswith("https") else "Invalid",
            "test_status": "Success",
            "health_score": health_score
        }

    except Exception:
        return {
            "status_code": 0,
            "response_time": 0,
            "ssl_status": "Unknown",
            "test_status": "Failed",
            "health_score": 0
        }

def check_broken_links(url: str):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a")

        total_links = len(links)
        broken_links = 0

        for link in links:
            href = link.get("href")

            if not href:
                continue

            if href.startswith("#"):
                continue

            if href.startswith("mailto:"):
                continue

            if href.startswith("tel:"):
                continue

            if href.startswith("/"):
                href = url.rstrip("/") + href

            try:
                r = requests.get(href, timeout=5)

                if r.status_code >= 400:
                    broken_links += 1

            except:
                broken_links += 1

        return {
            "total_links": total_links,
            "broken_links": broken_links
        }

    except Exception:
        return {
            "total_links": 0,
            "broken_links": 0
        }        
        