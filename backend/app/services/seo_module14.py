from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests

def seo_module14(url: str):
    print(f"[DEBUG] Starting SEO analysis for: {url}")
    try:
        # -----------------------
        # Render Website using Playwright
        # -----------------------
        print("[DEBUG] Launching Playwright browser...")
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

            # Wait for React hydration
            page.wait_for_timeout(5000)

            # Scroll to bottom to load lazy images
            page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            page.wait_for_timeout(3000)

            # Wait until images exist
            page.wait_for_selector("img", timeout=15000)
            html = page.content()
            browser.close()
            print("[DEBUG] Playwright rendering complete.")

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # -----------------------
        # robots.txt
        # -----------------------
        robots_url = url.rstrip("/") + "/robots.txt"
        print(f"[DEBUG] Fetching robots.txt: {robots_url}")
        robots = requests.get(
            robots_url,
            timeout=5
        )
        robots_exists = (
            robots.status_code == 200
        )

        sitemap_declared = False
        if robots_exists:
            sitemap_declared = (
                "Sitemap:" in robots.text
            )

        # -----------------------
        # sitemap.xml
        # -----------------------
        sitemap_url = url.rstrip("/") + "/sitemap.xml"
        print(f"[DEBUG] Fetching sitemap.xml: {sitemap_url}")
        sitemap = requests.get(
            sitemap_url,
            timeout=5
        )
        sitemap_exists = (
            sitemap.status_code == 200
        )

        # -----------------------
        # Google Analytics
        # -----------------------
        print("[DEBUG] Checking Google Analytics & GTM...")
        google_analytics = (
            "gtag(" in html
            or "G-" in html
            or "google-analytics" in html
        )

        # -----------------------
        # Google Tag Manager
        # -----------------------
        google_tag_manager = (
            "GTM-" in html
        )

        # -----------------------
        # Title
        # -----------------------
        print("[DEBUG] Extracting title...")
        title = soup.title
        title_text = ""
        title_length = 0

        if title:
            title_text = title.text.strip()
            title_length = len(
                title_text
            )

        # -----------------------
        # Meta Description
        # -----------------------
        print("[DEBUG] Extracting meta description...")
        meta_description = soup.find(
            "meta",
            attrs={
                "name":
                "description"
            }
        )
        description_exists = False
        description_length = 0

        if meta_description:
            description_exists = True
            description = meta_description.get(
                "content",
                ""
            )
            description_length = len(
                description
            )

        # -----------------------
        # Canonical
        # -----------------------
        print("[DEBUG] Checking Canonical URL...")
        canonical = soup.find(
            "link",
            attrs={
                "rel":
                "canonical"
            }
        )
        canonical_exists = False
        canonical_url = ""

        if canonical:
            canonical_exists = True
            canonical_url = canonical.get(
                "href",
                ""
            )

        # -----------------------
        # Favicon
        # -----------------------
        print("[DEBUG] Checking Favicon...")
        favicon = soup.find(
            "link",
            rel=lambda x: x and "icon" in x.lower()
        )
        favicon_exists = False
        favicon_url = ""

        if favicon:
            favicon_exists = True
            favicon_url = favicon.get("href", "")

        # -----------------------
        # Open Graph
        # -----------------------
        print("[DEBUG] Checking Open Graph tags...")
        og_title = soup.find(
            "meta",
            property="og:title"
        )
        og_description = soup.find(
            "meta",
            property="og:description"
        )
        og_image = soup.find(
            "meta",
            property="og:image"
        )
        og_url = soup.find(
            "meta",
            property="og:url"
        )
        og_type = soup.find(
            "meta",
            property="og:type"
        )

        # -----------------------
        # Twitter Card
        # -----------------------
        print("[DEBUG] Checking Twitter Cards...")
        twitter_card = soup.find(
            "meta",
            attrs={
                "name": "twitter:card"
            }
        )

        # -----------------------
        # Structured Data
        # -----------------------
        print("[DEBUG] Analyzing Structured Data...")
        schema_scripts = soup.find_all(
            "script",
            attrs={
                "type": "application/ld+json"
            }
        )
        structured_data = len(schema_scripts) > 0
        schema_types = []

        for script in schema_scripts:
            text = script.string
            if not text:
                continue
            if "Organization" in text:
                schema_types.append("Organization")
            if "Product" in text:
                schema_types.append("Product")
            if "Article" in text:
                schema_types.append("Article")
            if "BreadcrumbList" in text:
                schema_types.append("BreadcrumbList")
            if "FAQPage" in text:
                schema_types.append("FAQPage")

        schema_types = list(set(schema_types))

        # -----------------------
        # Mobile Friendly
        # -----------------------
        print("[DEBUG] Checking Mobile Friendly tags...")
        viewport = soup.find(
            "meta",
            attrs={
                "name": "viewport"
            }
        )
        mobile_friendly = False

        if viewport:
            content = viewport.get(
                "content",
                ""
            ).lower()
            if "width=device-width" in content:
                mobile_friendly = True

        # -----------------------
        # Language
        # -----------------------
        print("[DEBUG] Checking Language tags...")
        html_tag = soup.find("html")
        language = ""
        lang_exists = False

        if html_tag:
            language = html_tag.get(
                "lang",
                ""
            )
            if language:
                lang_exists = True

       # -----------------------
        # Images (Advanced Detection)
        # -----------------------
        print("[DEBUG] Analyzing Images...")
        images = []

        # Normal img tags
        images.extend(soup.find_all("img"))

        # picture > source
        for picture in soup.find_all("picture"):
            images.extend(picture.find_all("source"))

        # Remove duplicates
        images = list(dict.fromkeys(images))
        total_images = len(images)

        missing_alt = 0
        lazy_loaded = 0
        missing_dimensions = 0

        for img in images:
            # ---------- image source ----------
            src = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-lazy-src")
                or img.get("srcset")
                or ""
            )

            if not src:
                continue

            # ---------- alt ----------
            if img.name == "img":
                if not img.get("alt"):
                    missing_alt += 1

            # ---------- lazy ----------
            if (
                img.get("loading") == "lazy"
                or img.get("data-src")
                or img.get("data-lazy-src")
            ):
                lazy_loaded += 1

            # ---------- dimensions ----------
            if img.name == "img":
                if not img.get("width") or not img.get("height"):
                    missing_dimensions += 1
        
        # -----------------------
        # Headings
        # -----------------------
        print("[DEBUG] Analyzing Headings...")
        h1_tags = soup.find_all("h1")
        h2_tags = soup.find_all("h2")

        h1_count = len(h1_tags)
        h2_count = len(h2_tags)

        h1_text = [
            h.get_text(strip=True)
            for h in h1_tags
        ]

        # -----------------------
        # SEO Score
        # -----------------------
        print("[DEBUG] Calculating SEO Score...")
        score = 0

        if robots_exists: score += 10
        if sitemap_exists: score += 10
        if google_analytics: score += 10
        if google_tag_manager: score += 5
        if title_text: score += 5
        if description_exists: score += 5
        if canonical_exists: score += 5
        if favicon_exists: score += 5
        if og_title: score += 5
        if og_description: score += 5
        if og_image: score += 5
        if twitter_card: score += 5
        if structured_data: score += 10
        if mobile_friendly: score += 5
        if lang_exists: score += 5
        if h1_count > 0: score += 5
        if total_images > 0 and missing_alt == 0: score += 5

        if score > 100:
            score = 100
            
        print(f"[DEBUG] Final SEO Score: {score}")

        # -----------------------
        # Return
        # -----------------------
        print("[DEBUG] Returning successful results.")
        return {
            "module": "SEO Analysis",
            "status": "PASS" if score >= 80 else "FAIL",

            "seo_score": score,

            "robots_txt": robots_exists,
            "robots_has_sitemap": sitemap_declared,
            "sitemap_xml": sitemap_exists,

            "google_analytics": google_analytics,
            "google_tag_manager": google_tag_manager,

            "mobile_friendly": mobile_friendly,
            "viewport": viewport is not None,

            "language": language,
            "lang_tag": lang_exists,

            "title": title_text,
            "title_length": title_length,

            "meta_description": description_exists,
            "description_length": description_length,

            "canonical": canonical_exists,
            "canonical_url": canonical_url,

            "favicon": favicon_exists,
            "favicon_url": favicon_url,

            "open_graph": {
                "title": og_title is not None,
                "description": og_description is not None,
                "image": og_image is not None,
                "url": og_url is not None,
                "type": og_type is not None
            },

            "twitter_card": twitter_card is not None,

            "structured_data": structured_data,
            "schema_types": schema_types,

            "h1_count": h1_count,
            "h2_count": h2_count,
            "h1_text": h1_text,

            "image_seo": {
                "total_images": total_images,
                "missing_alt": missing_alt,
                "lazy_loaded": lazy_loaded,
                "missing_dimensions": missing_dimensions
            },

            "issues": [],
            "recommendations": [],

            "screenshots": [
                "screenshots\\seo_module14.png"
            ]
        }

    except Exception as e:
        print(f"[DEBUG] Error occurred: {str(e)}")
        return {
            "module": "SEO Analysis",
            "status": "FAIL",
            "seo_score": 0,
            "issues": [str(e)],
            "recommendations": [
                "Unable to complete SEO analysis."
            ],
            "screenshots": []
        }

# Functional Testing Service Call
# url = "https://example.com"
# results = []
# seo14 = seo_module14(url)
# results.append(seo14)
# print(results)