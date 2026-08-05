import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def performance_check(url: str):
    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)

            page = browser.new_page()

            start = time.time()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(5000)

            page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
            """)

            page.wait_for_timeout(3000)

            html = page.content()

            end = time.time()

            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        images = soup.find_all("img")
        scripts = soup.find_all("script")
        css = soup.find_all("link", rel="stylesheet")

        page_size = round(len(html.encode("utf-8")) / 1024, 2)

        total_requests = (
            len(images)
            + len(scripts)
            + len(css)
        )

        load_time = round(end - start, 2)

        score = 100

        issues = []
        recommendations = []

        if load_time > 3:
            score -= 20
            issues.append("Page load time is too high.")
            recommendations.append(
                "Optimize images, enable caching and minify CSS/JavaScript."
            )

        if page_size > 2000:
            score -= 20
            issues.append("Large page size detected.")
            recommendations.append(
                "Compress images and reduce HTML/CSS/JS size."
            )

        if total_requests > 100:
            score -= 20
            issues.append("Too many HTTP requests.")
            recommendations.append(
                "Combine CSS/JS files and remove unused assets."
            )

        if score < 0:
            score = 0

        if not issues:
            recommendations.append(
                "Website performance looks good. Continue monitoring regularly."
            )

        return {
            "page_load_time": load_time,
            "page_size_kb": page_size,
            "total_requests": total_requests,
            "images": len(images),
            "scripts": len(scripts),
            "css_files": len(css),
            "performance_score": score,
            "issues": issues,
            "recommendations": recommendations
        }

    except Exception as e:

        return {
            "page_load_time": 0,
            "page_size_kb": 0,
            "total_requests": 0,
            "images": 0,
            "scripts": 0,
            "css_files": 0,
            "performance_score": 0,
            "issues": [str(e)],
            "recommendations": [
                "Verify the website URL or internet connection."
            ],
            "error": str(e)
        }