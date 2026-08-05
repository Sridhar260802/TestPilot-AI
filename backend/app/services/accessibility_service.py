from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def accessibility_check(url: str):

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)

            page = browser.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(5000)

            page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            page.wait_for_timeout(3000)

            html = page.content()

            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        images = soup.find_all("img")
        buttons = soup.find_all("button")
        forms = soup.find_all("form")
        inputs = soup.find_all("input")

        images_without_alt = 0
        buttons_without_text = 0
        inputs_without_label = 0

        issues = []
        recommendations = []

        # -----------------------
        # Images
        # -----------------------

        for img in images:
            if not img.get("alt"):
                images_without_alt += 1

        if images_without_alt > 0:
            issues.append(
                f"{images_without_alt} image(s) missing ALT text."
            )
            recommendations.append(
                "Add descriptive ALT text to every image."
            )

        # -----------------------
        # Buttons
        # -----------------------

        for btn in buttons:
            if not btn.get_text(strip=True):
                buttons_without_text += 1

        if buttons_without_text > 0:
            issues.append(
                f"{buttons_without_text} button(s) missing visible text."
            )
            recommendations.append(
                "Provide accessible text for buttons."
            )

        # -----------------------
        # Inputs
        # -----------------------

        for field in inputs:

            field_id = field.get("id")
            has_label = False

            if field_id:
                label = soup.find(
                    "label",
                    attrs={"for": field_id}
                )

                if label:
                    has_label = True

            if not has_label:
                inputs_without_label += 1

        if inputs_without_label > 0:
            issues.append(
                f"{inputs_without_label} input field(s) missing labels."
            )
            recommendations.append(
                "Associate every input field with a label."
            )

        # -----------------------
        # Score
        # -----------------------

        score = 100

        score -= images_without_alt * 5
        score -= buttons_without_text * 10
        score -= inputs_without_label * 5

        if score < 0:
            score = 0

        # -----------------------
        # Default Recommendations
        # -----------------------

        if not recommendations:
            recommendations = [
                "No accessibility issues detected."
            ]
        return {

            "total_images": len(images),

            "images_without_alt": images_without_alt,

            "buttons": len(buttons),

            "buttons_without_text": buttons_without_text,

            "forms": len(forms),

            "inputs": len(inputs),

            "inputs_without_label": inputs_without_label,

            "accessibility_score": score,

            "issues": issues,

            "recommendations": recommendations

        }

    except Exception as e:

        return {

            "total_images": 0,

            "images_without_alt": 0,

            "buttons": 0,

            "buttons_without_text": 0,

            "forms": 0,

            "inputs": 0,

            "inputs_without_label": 0,

            "accessibility_score": 0,

            "issues": [],

            "recommendations": [],

            "error": str(e)

        }