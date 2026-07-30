from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def accessibility_check(url: str):

    try:
        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )
            page.wait_for_timeout(5000)
            page.screenshot(
                path="debug.png",
                full_page=True
            )
            print(page.content()) 
            page.evaluate("""window.scrollTo(0,document.body.scrollHeight);""")
            page.wait_for_timeout(3000)
            html = page.content()

            browser.close()


        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        images = soup.find_all("img")
        buttons = soup.find_all("button")
        forms = soup.find_all("form")


        images_without_alt = sum(
            1 for img in images
            if not img.get("alt")
        )


        buttons_without_text = sum(
            1 for btn in buttons
            if not btn.text.strip()
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


    except Exception as e:

        return {
            "total_images": 0,
            "images_without_alt": 0,
            "buttons": 0,
            "buttons_without_text": 0,
            "forms": 0,
            "accessibility_score": 0,
            "error": str(e)
        }