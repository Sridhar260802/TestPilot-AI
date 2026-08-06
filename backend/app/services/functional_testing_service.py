from unittest import result
from playwright.sync_api import TimeoutError
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import os
import time

# =====================================
# Default Credentials
# =====================================

TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "Password123!")

# =====================================
# Screenshot Folder
# =====================================

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# =====================================
# Screenshot Helper
# =====================================

def save_screenshot(page, filename):
    path = os.path.join(SCREENSHOT_DIR, filename)

    try:
        page.screenshot(
            path=path,
            full_page=True
        )
    except:
        pass

    return path


# =====================================
# Default Result
# =====================================

def create_result(module_name):

    return {
        "module": module_name,
        "status": "PASS",
        "page_load_time": 0,
        "performance": "",
        "issue": "",
        "possible_reason": "",
        "recommendation": "",
        "developer_action": "",
        "screenshot": ""
    }


# =====================================
# Module 1
# Website Opens
# =====================================

def website_open_test(page, url):

    result = create_result("Website Opens")

    try:

        print(f"\nLoading Website : {url}")

        start_time = time.time()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        # React / NextJS Hydration
        page.wait_for_timeout(5000)

        page.wait_for_load_state("networkidle")

        load_time = round(
            time.time() - start_time,
            2
        )

        result["page_load_time"] = load_time

        print(f"Load Time : {load_time} sec")

        response = page.goto(
            url,
            wait_until="networkidle"
        )

        if response is None:

            result["status"] = "FAIL"

            result["issue"] = "Website did not respond."

            result["possible_reason"] = "Server unavailable."

            result["recommendation"] = "Verify hosting."

            result["developer_action"] = "Check deployment."

            result["screenshot"] = save_screenshot(
                page,
                "website_open_failed.png"
            )

            return result

        if response.status >= 400:

            result["status"] = "FAIL"

            result["issue"] = f"HTTP Status : {response.status}"

            result["possible_reason"] = "Server Error"

            result["recommendation"] = "Verify backend deployment."

            result["developer_action"] = "Check server logs."

            result["screenshot"] = save_screenshot(
                page,
                "website_http_error.png"
            )

            return result

        title = page.title().strip()

        if title == "":

            result["status"] = "FAIL"

            result["issue"] = "Page title empty."

            result["possible_reason"] = "Frontend failed."

            result["recommendation"] = "Verify React build."

            result["developer_action"] = "Check frontend."

            result["screenshot"] = save_screenshot(
                page,
                "website_title_error.png"
            )

            return result

        # Performance Rating

        if load_time <= 2:

            result["performance"] = "Excellent"

        elif load_time <= 4:

            result["performance"] = "Good"

        elif load_time <= 6:

            result["performance"] = "Average"

        else:

            result["performance"] = "Slow"

            result["recommendation"] = (
                "Optimize CSS, JS, Images, Lazy Loading."
            )

            result["developer_action"] = (
                "Enable Cache, CDN & Compression."
            )

        result["screenshot"] = save_screenshot(
            page,
            "website_open_success.png"
        )

        print("Website Loaded Successfully")

        return result

    except Exception as e:

        result["status"] = "FAIL"

        result["issue"] = str(e)

        result["possible_reason"] = "Unexpected Exception"

        result["recommendation"] = "Verify website."

        result["developer_action"] = "Check logs."

        try:

            result["screenshot"] = save_screenshot(
                page,
                "website_exception.png"
            )

        except:
            pass

        return result

# =====================================
# Module 2
# Navigation Links
# =====================================

def navigation_links_test(page, url):

    result = create_result("Navigation Links")

    try:

        # Wait for React rendering
        page.wait_for_timeout(3000)

        page.wait_for_load_state("networkidle")

        # Find all links
        links = page.locator("a[href]")

        total_links = links.count()

        print(f"Found {total_links} navigation links")

        broken_links = []
        empty_links = []

        for i in range(total_links):

            try:

                link = links.nth(i)

                href = link.get_attribute("href")

                if href is None or href.strip() == "":

                    empty_links.append(
                        f"Link {i+1}"
                    )

                    continue

                if href.startswith("#"):
                    continue

                if href.startswith("javascript"):
                    continue

                if href.startswith("mailto:"):
                    continue

                if href.startswith("tel:"):
                    continue

                full_url = urljoin(url, href)

                response = page.request.get(
                    full_url,
                    timeout=10000
                )

                if response.status >= 400:

                    broken_links.append({
                        "url": full_url,
                        "status": response.status
                    })

            except Exception:

                broken_links.append({
                    "url": href,
                    "status": "No Response"
                })

        result["total_links"] = total_links
        result["broken_links"] = len(broken_links)
        result["empty_links"] = len(empty_links)

        if broken_links or empty_links:

            result["status"] = "FAIL"

            issue = []

            if broken_links:

                issue.append(
                    f"{len(broken_links)} Broken Links"
                )

            if empty_links:

                issue.append(
                    f"{len(empty_links)} Empty Links"
                )

            result["issue"] = ", ".join(issue)

            result["possible_reason"] = (
                "Broken href or invalid routing."
            )

            result["recommendation"] = (
                "Verify all navigation links."
            )

            result["developer_action"] = (
                "Update routing or broken URLs."
            )

            result["details"] = broken_links

            result["screenshot"] = save_screenshot(
                page,
                "navigation_links_failed.png"
            )

        else:

            result["status"] = "PASS"

            result["screenshot"] = save_screenshot(
                page,
                "navigation_links_success.png"
            )

        print(
            f"Navigation Completed | Total:{total_links} "
            f"Broken:{len(broken_links)} Empty:{len(empty_links)}"
        )

        return result

    except Exception as e:

        result["status"] = "FAIL"

        result["issue"] = str(e)

        result["possible_reason"] = (
            "Navigation testing exception."
        )

        result["recommendation"] = (
            "Verify navigation."
        )

        result["developer_action"] = (
            "Review frontend routing."
        )

        try:

            result["screenshot"] = save_screenshot(
                page,
                "navigation_links_exception.png"
            )

        except:
            pass

        return result  
    
# =====================================
# Module 3
# Navbar Testing
# =====================================

def navbar_test(page):

    result = create_result("Navbar")

    try:

        # Wait for React rendering
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        # Multiple navbar selectors
        navbar = page.locator(
            "nav, header, .navbar, .header, [role='navigation']"
        ).first

        if navbar.count() == 0:

            result["status"] = "FAIL"
            result["issue"] = "Navbar not found."
            result["possible_reason"] = "Navbar missing."
            result["recommendation"] = "Create navigation bar."
            result["developer_action"] = "Verify Header component."
            result["screenshot"] = save_screenshot(
                page,
                "navbar_missing.png"
            )

            return result

        print("Navbar Found")

        # ----------------------------
        # Logo Check
        # ----------------------------

        logo = navbar.locator("img")

        result["logo_found"] = logo.count() > 0

        # ----------------------------
        # Navbar Links
        # ----------------------------

        nav_links = navbar.locator("a[href]")

        total_links = nav_links.count()

        failed_links = []

        for i in range(total_links):

            try:

                link = nav_links.nth(i)

                if not link.is_visible():

                    failed_links.append(
                        f"Hidden Link {i+1}"
                    )

                    continue

                href = link.get_attribute("href")

                if href is None:
                    continue

                if href.startswith("#"):
                    continue

                if href.startswith("javascript"):
                    continue

                response = page.request.get(
                    urljoin(page.url, href),
                    timeout=5000
                )

                if response.status >= 400:

                    failed_links.append(
                        f"{href} ({response.status})"
                    )

            except Exception as e:

                failed_links.append(
                    f"Link {i+1} ({str(e)})"
                )

        # ----------------------------
        # Sticky Navbar
        # ----------------------------

        sticky = page.evaluate("""
        () => {

            const nav =
                document.querySelector(
                    "nav,header,.navbar,.header,[role='navigation']"
                );

            if(!nav)
                return false;

            const style =
                window.getComputedStyle(nav);

            return style.position==="fixed" ||
                   style.position==="sticky";

        }
        """)

        result["sticky_navbar"] = sticky
        result["total_links"] = total_links
        result["failed_links"] = len(failed_links)
        result["failed_items"] = failed_links

        # ----------------------------
        # Mobile Menu
        # ----------------------------

        mobile_menu = page.locator("""
        button[aria-label*='menu'],
        button[aria-label*='Menu'],
        .menu-toggle,
        .hamburger
        """)

        result["mobile_menu"] = mobile_menu.count() > 0

        # ----------------------------
        # Final Result
        # ----------------------------

        if failed_links:

            result["status"] = "FAIL"

            result["issue"] = (
                f"{len(failed_links)} Navbar link(s) failed."
            )

            result["possible_reason"] = (
                "Broken routing."
            )

            result["recommendation"] = (
                "Verify Navbar links."
            )

            result["developer_action"] = (
                "Fix Header routing."
            )

            result["screenshot"] = save_screenshot(
                page,
                "navbar_failed.png"
            )

        else:

            result["status"] = "PASS"

            result["screenshot"] = save_screenshot(
                page,
                "navbar_success.png"
            )

        print(
            f"Navbar Checked | Links : {total_links} | Failed : {len(failed_links)}"
        )

        return result

    except Exception as e:

        result["status"] = "FAIL"

        result["issue"] = str(e)

        result["possible_reason"] = "Navbar testing exception."

        result["recommendation"] = "Verify navbar."

        result["developer_action"] = "Review Header component."

        try:

            result["screenshot"] = save_screenshot(
                page,
                "navbar_exception.png"
            )

        except:
            pass

        return result
    
# =====================================
# Module 4
# Footer Testing
# =====================================

def footer_test(page, url):

    result = create_result("Footer")

    try:

        print("\n========== FOOTER TEST START ==========")

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        print("Searching Footer...")

        footer = page.locator(
            "footer, .footer, #footer"
        ).first

        if footer.count() == 0:

            print("❌ Footer NOT Found")

            result["status"] = "FAIL"
            result["issue"] = "Footer not found."
            result["possible_reason"] = "Footer missing."
            result["recommendation"] = "Add footer section."
            result["developer_action"] = "Verify Footer component."
            result["screenshot"] = save_screenshot(
                page,
                "footer_missing.png"
            )

            return result

        print("✅ Footer Found")

        if not footer.is_visible():

            print("❌ Footer Hidden")

            result["status"] = "FAIL"
            result["issue"] = "Footer not visible."
            result["possible_reason"] = "CSS issue."
            result["recommendation"] = "Display footer correctly."
            result["developer_action"] = "Check Footer CSS."
            result["screenshot"] = save_screenshot(
                page,
                "footer_hidden.png"
            )

            return result

        # -----------------------------
        # Footer Links
        # -----------------------------

        links = footer.locator("a[href]")

        total_links = links.count()

        print(f"Footer Links Found : {total_links}")

        broken_links = []

        for i in range(total_links):

            try:

                href = links.nth(i).get_attribute("href")

                print(f"[{i+1}] Checking -> {href}")

                if href is None:
                    continue

                if href.startswith("#"):
                    continue

                if href.startswith("javascript"):
                    continue

                if href.startswith("mailto:"):
                    continue

                if href.startswith("tel:"):
                    continue

                full_url = urljoin(url, href)

                response = page.request.get(
                    full_url,
                    timeout=5000
                )

                print(
                    f"Status : {response.status}"
                )

                if response.status >= 400:

                    broken_links.append(
                        {
                            "url": full_url,
                            "status": response.status
                        }
                    )

            except Exception as e:

                print(
                    f"Broken : {href}"
                )

                print(e)

                broken_links.append(
                    {
                        "url": href,
                        "status": "No Response"
                    }
                )

        # -----------------------------
        # Social Links
        # -----------------------------

        social_links = footer.locator(
            """
            a[href*='facebook'],
            a[href*='instagram'],
            a[href*='linkedin'],
            a[href*='twitter'],
            a[href*='youtube']
            """
        ).count()

        print(
            f"Social Links : {social_links}"
        )

        # -----------------------------
        # Contact Details
        # -----------------------------

        contact_found = footer.locator(
            "text=/@|\\+91|gmail|phone|contact/i"
        ).count()

        print(
            f"Contact Found : {contact_found}"
        )

        # -----------------------------
        # Copyright
        # -----------------------------

        copyright_found = footer.locator(
            "text=/copyright|©/i"
        ).count()

        print(
            f"Copyright : {copyright_found}"
        )

        result["footer_links"] = total_links
        result["broken_links"] = len(broken_links)
        result["social_links"] = social_links
        result["contact_found"] = contact_found > 0
        result["copyright_found"] = copyright_found > 0

        if broken_links:

            print(
                f"❌ Broken Links : {len(broken_links)}"
            )

            result["status"] = "FAIL"
            result["issue"] = f"{len(broken_links)} Broken Footer Links."
            result["possible_reason"] = "Invalid URL."
            result["recommendation"] = "Update Footer Links."
            result["developer_action"] = "Verify Footer Routing."
            result["details"] = broken_links
            result["screenshot"] = save_screenshot(
                page,
                "footer_failed.png"
            )

        else:

            print("✅ Footer Passed")

            result["status"] = "PASS"

            result["screenshot"] = save_screenshot(
                page,
                "footer_success.png"
            )

        print("========== FOOTER TEST END ==========\n")

        return result

    except Exception as e:

        print("Footer Exception")

        print(e)

        result["status"] = "FAIL"
        result["issue"] = str(e)
        result["possible_reason"] = "Footer testing exception."
        result["recommendation"] = "Verify Footer."
        result["developer_action"] = "Review Footer."

        try:

            result["screenshot"] = save_screenshot(
                page,
                "footer_exception.png"
            )

        except:
            pass

        return result
    
# =====================================
# Module 5
# Buttons Testing
# =====================================

def buttons_test(page):

    result = create_result("Buttons")

    try:

        print("\n========== BUTTON TEST START ==========")

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        buttons = page.locator(
            "button:visible, input[type='submit']:visible, input[type='button']:visible, a[role='button']:visible"
        )

        button_names = []

        for i in range(buttons.count()):

            try:

                txt = buttons.nth(i).inner_text().strip()

                if txt != "" and txt not in button_names:

                    button_names.append(txt)

            except:
                pass

        print(f"Unique Visible Buttons : {len(button_names)}")

        if len(button_names) == 0:

            print("❌ No Buttons Found")

            result["status"] = "FAIL"
            result["issue"] = "No buttons found."
            result["possible_reason"] = "UI missing."
            result["recommendation"] = "Verify frontend."
            result["developer_action"] = "Check components."
            result["screenshot"] = save_screenshot(
                page,
                "buttons_missing.png"
            )

            return result

        failed_buttons = []
        passed_buttons = []
        js_errors = []

        page.on(
            "pageerror",
            lambda err: js_errors.append(str(err))
        )

        for i, name in enumerate(button_names):

            print(f"\nChecking Button : {i+1}")
            print(f"Text : {name}")

            button = page.get_by_text(name, exact=True).first

            try:

                text = button.inner_text().strip()

                if text == "":
                    text = f"Button {i+1}"

                print("\n--------------------------------")
                print(f"Checking Button : {i+1}")
                print(f"Text : {text}")

                # Visible

                visible = button.is_visible()
                print(f"Visible : {visible}")

                if not visible:

                    print("❌ Hidden")

                    failed_buttons.append(
                        f"{text} (Hidden)"
                    )

                    continue

                # Enabled

                enabled = button.is_enabled()
                print(f"Enabled : {enabled}")

                if not enabled:

                    print("❌ Disabled")

                    failed_buttons.append(
                        f"{text} (Disabled)"
                    )

                    continue

                # Click

                print("Clicking...")

                original_url = page.url

                button.click(
                    timeout=5000,
                    force=True,
                    no_wait_after=True
                )

                page.wait_for_timeout(3000)

                current_url = page.url

                print(f"Before URL : {original_url}")
                print(f"After URL  : {current_url}")

                if current_url != original_url:

                    print("✅ Redirect Working")

                    passed_buttons.append(text)

                    # Return back to original page
                    page.goto(
                        original_url,
                        wait_until="networkidle"
                    )

                    page.wait_for_timeout(2000)

                else:

                    print("❌ No Redirect")

                    failed_buttons.append(
                        f"{text} (No Redirect)"
                    )

            except Exception as e:

                print("❌ Click Failed")
                print(e)

                failed_buttons.append(
                    f"{text} ({str(e)})"
                )

        print("\n================================")
        print(f"Passed Buttons : {len(passed_buttons)}")
        print(f"Failed Buttons : {len(failed_buttons)}")
        print("================================")

        result["total_buttons"] = len(button_names)
        result["passed_buttons"] = len(passed_buttons)
        result["failed_buttons"] = len(failed_buttons)
        result["javascript_errors"] = js_errors

        if failed_buttons:

            result["status"] = "FAIL"
            result["issue"] = (
                f"{len(failed_buttons)} Button(s) Failed."
            )
            result["possible_reason"] = (
                "Button click issue."
            )
            result["recommendation"] = (
                "Verify onclick / routing."
            )
            result["developer_action"] = (
                "Fix frontend."
            )
            result["details"] = failed_buttons

            result["screenshot"] = save_screenshot(
                page,
                "buttons_failed.png"
            )

        else:

            result["status"] = "PASS"

            result["screenshot"] = save_screenshot(
                page,
                "buttons_success.png"
            )

        print("========== BUTTON TEST END ==========\n")

        return result

    except Exception as e:

        print("\n❌ BUTTON MODULE EXCEPTION")
        print(e)

        result["status"] = "FAIL"
        result["issue"] = str(e)
        result["possible_reason"] = "Button testing exception."
        result["recommendation"] = "Verify buttons."
        result["developer_action"] = "Review frontend."

        try:

            result["screenshot"] = save_screenshot(
                page,
                "buttons_exception.png"
            )

        except:
            pass

        return result    
    
    
    
# =====================================
# Module 6
# Form Validation (Part 6.1)
# =====================================

def form_validation_test(page):

    result = create_result("Form Validation")

    try:

        print("\n========== FORM VALIDATION START ==========")

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        # -----------------------------
        # Detect Forms
        # -----------------------------

        forms = page.locator("form")

        total_forms = forms.count()

        print(f"Total Forms Found : {total_forms}")

        # Fallback (React apps)
        if total_forms == 0:

            print("No <form> tag found.")
            print("Searching Input Groups...")

            forms = page.locator(
                "input, textarea, select"
            )

            if forms.count() > 0:

                total_forms = 1

                print("Input controls detected.")

        if total_forms == 0:

            result["status"] = "FAIL"

            result["issue"] = "No Forms Found"

            result["possible_reason"] = "Website has no forms."

            result["recommendation"] = "Verify Login / Contact Form."

            result["developer_action"] = "Check frontend forms."

            result["screenshot"] = save_screenshot(
                page,
                "form_missing.png"
            )

            return result

        # -----------------------------
        # Collect Inputs
        # -----------------------------

        inputs = page.locator(
            "input, textarea, select"
        )

        total_inputs = inputs.count()

        print(f"Total Inputs : {total_inputs}")

        input_details = []

        for i in range(total_inputs):

            try:

                control = inputs.nth(i)

                input_type = control.get_attribute("type")

                if input_type is None:
                    input_type = "text"

                placeholder = control.get_attribute("placeholder") or ""

                name = control.get_attribute("name") or ""

                required = control.get_attribute("required")

                visible = control.is_visible()

                enabled = control.is_enabled()

                print(
                    f"[{i+1}] "
                    f"Type={input_type} | "
                    f"Name={name} | "
                    f"Placeholder={placeholder}"
                )

                input_details.append({

                    "type": input_type,

                    "name": name,

                    "placeholder": placeholder,

                    "required": required is not None,

                    "visible": visible,

                    "enabled": enabled

                })

            except Exception as e:

                print(e)

        result["total_forms"] = total_forms
        result["total_inputs"] = total_inputs
        result["input_details"] = input_details

        result["status"] = "PASS"

        result["screenshot"] = save_screenshot(
            page,
            "form_detect_success.png"
        )

        print("========== FORM DETECTION COMPLETED ==========\n")

        # -----------------------------
        # Required Field Validation
        # -----------------------------

        print("\n========== REQUIRED FIELD VALIDATION ==========")

        required_failed = []

        for i in range(total_inputs):

            try:

                control = inputs.nth(i)

                input_type = control.get_attribute("type") or "text"

                name = control.get_attribute("name") or ""

                placeholder = control.get_attribute("placeholder") or ""

                required = control.get_attribute("required")

                visible = control.is_visible()

                enabled = control.is_enabled()

                field_name = (
                    name
                    if name != ""
                    else placeholder
                    if placeholder != ""
                    else f"Field {i+1}"
                )

                print("--------------------------------")
                print(f"Checking : {field_name}")
                print(f"Type      : {input_type}")
                print(f"Visible   : {visible}")
                print(f"Enabled   : {enabled}")
                print(f"Required  : {required is not None}")

                if not visible:

                    print("❌ Hidden Field")

                    required_failed.append(
                        f"{field_name} (Hidden)"
                    )

                    continue

                if not enabled:

                    print("❌ Disabled Field")

                    required_failed.append(
                        f"{field_name} (Disabled)"
                    )

                    continue

                if required is not None:

                    print("Testing Empty Validation...")

                    control.fill("")

                    control.press("Tab")

                    page.wait_for_timeout(300)

                    valid = page.evaluate("""
                    (el)=>{
                        return el.checkValidity();
                    }
                    """, control.element_handle())

                    print(f"HTML Validation : {valid}")

                    if valid:

                        print("❌ Required validation NOT working")

                        required_failed.append(
                            f"{field_name} (Required Validation Failed)"
                        )

                    else:

                        print("✅ Required validation Working")

            except Exception as e:

                print(e)

                required_failed.append(
                    f"Field {i+1} ({str(e)})"
                )

        print("\n======================================")
        print(f"Required Validation Failed : {len(required_failed)}")
        print("======================================")

        result["required_validation_failed"] = len(required_failed)
        result["required_validation_details"] = required_failed

        # -----------------------------
        # Email / Phone / Password Validation
        # -----------------------------

        print("\n========== EMAIL / PHONE / PASSWORD VALIDATION ==========")

        validation_failed = []

        for i in range(total_inputs):

            try:

                control = inputs.nth(i)

                input_type = (control.get_attribute("type") or "").lower()

                name = (control.get_attribute("name") or "").lower()

                placeholder = (control.get_attribute("placeholder") or "").lower()

                field = f"{name} {placeholder}"

                # -----------------------------
                # EMAIL
                # -----------------------------
                if input_type == "email" or "email" in field:

                    print("\n--------------------------------")
                    print("Checking EMAIL Validation")

                    control.fill("abc")

                    control.press("Tab")

                    page.wait_for_timeout(500)

                    valid = page.evaluate("""
                    (el)=>{
                        return el.checkValidity();
                    }
                    """, control.element_handle())

                    print(f"Entered : abc")
                    print(f"Validation : {valid}")

                    if valid:

                        print("❌ Invalid Email Accepted")

                        validation_failed.append(
                            "Email Validation Failed"
                        )

                    else:

                        print("✅ Email Validation Working")

                # -----------------------------
                # PHONE
                # -----------------------------
                elif input_type == "tel" or "phone" in field or "mobile" in field:

                    print("\n--------------------------------")
                    print("Checking PHONE Validation")

                    control.fill("123")

                    control.press("Tab")

                    page.wait_for_timeout(500)

                    value = control.input_value()

                    print(f"Entered : {value}")

                    if len(value) < 10:

                        print("✅ Phone Validation Working")

                    else:

                        print("❌ Phone Validation Failed")

                        validation_failed.append(
                            "Phone Validation Failed"
                        )

                # -----------------------------
                # PASSWORD
                # -----------------------------
                elif input_type == "password":

                    print("\n--------------------------------")
                    print("Checking PASSWORD Validation")

                    control.fill("123")

                    control.press("Tab")

                    page.wait_for_timeout(500)

                    value = control.input_value()

                    print(f"Entered : {value}")

                    if len(value) < 6:

                        print("✅ Password Rule Triggered")

                    else:

                        print("❌ Weak Password Accepted")

                        validation_failed.append(
                            "Password Validation Failed"
                        )

            except Exception as e:

                print(e)

                validation_failed.append(str(e))

        print("\n======================================")
        print(f"Validation Failed : {len(validation_failed)}")
        print("======================================")

        result["validation_failed"] = len(validation_failed)
        result["validation_details"] = validation_failed

        # -----------------------------
        # Form Submit Validation
        # -----------------------------

        print("\n========== FORM SUBMIT VALIDATION ==========")

        submit_failed = []

        try:

            submit_buttons = page.locator(
                "button[type='submit'], input[type='submit']"
            )

            total_submit = submit_buttons.count()

            print(f"Submit Buttons Found : {total_submit}")

            if total_submit == 0:

                print("⚠ No Submit Button Found")

                result["submit_button"] = False

            else:

                submit = submit_buttons.first

                print("Clicking Submit Button...")

                submit.click(force=True)

                page.wait_for_timeout(3000)

                # -----------------------------
                # Success Message
                # -----------------------------

                success = page.locator(
                    "text=/success|submitted|thank you|completed/i"
                )

                success_found = success.count() > 0

                print(f"Success Message : {success_found}")

                # -----------------------------
                # Error Message
                # -----------------------------

                error = page.locator(
                    "text=/required|invalid|error|failed/i"
                )

                error_found = error.count() > 0

                print(f"Error Message : {error_found}")

                result["submit_button"] = True
                result["success_message"] = success_found
                result["error_message"] = error_found

                if success_found:

                    print("✅ Form Submitted Successfully")

                elif error_found:

                    print("⚠ Validation Error Displayed")

                else:

                    print("❌ No Response After Submit")

                    submit_failed.append(
                        "No Success/Error Message"
                    )

        except Exception as e:

            print("❌ Submit Exception")
            print(e)

            submit_failed.append(str(e))

        print("\n======================================")
        print(f"Submit Failed : {len(submit_failed)}")
        print("======================================")

        result["submit_failed"] = len(submit_failed)
        result["submit_details"] = submit_failed

        return result

    except Exception as e:

        print(e)

        result["status"] = "FAIL"

        result["issue"] = str(e)

        result["possible_reason"] = "Form Detection Exception"

        result["recommendation"] = "Verify Forms."

        result["developer_action"] = "Review frontend."

        try:

            result["screenshot"] = save_screenshot(
                page,
                "form_exception.png"
            )

        except:
            pass

        return result

# =====================================
# Module 6.5
# Broken Images
# =====================================

def broken_images_test(page):

    result = create_result("Broken Images")

    try:

        print("\n========== BROKEN IMAGES TEST START ==========")

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        images = page.locator("img")

        total_images = images.count()

        print(f"Total Images Found : {total_images}")

        broken_images = []

        for i in range(total_images):

            try:

                img = images.nth(i)

                src = img.get_attribute("src")

                if not src:
                    print(f"[{i+1}] Image has no src")
                    broken_images.append("Missing src")
                    continue

                print(f"[{i+1}] Checking : {src}")

                is_loaded = page.evaluate(
                    """
                    (element) => {
                        return element.complete &&
                               element.naturalWidth > 0;
                    }
                    """,
                    img
                )

                if not is_loaded:

                    print("❌ Broken Image")

                    broken_images.append(src)

                else:

                    print("✅ Image Loaded")

            except Exception as e:

                print(f"❌ Exception : {e}")

                broken_images.append(str(e))

        result["total_images"] = total_images
        result["broken_images"] = len(broken_images)

        if broken_images:

            print(f"\nBroken Images : {len(broken_images)}")

            result["status"] = "FAIL"
            result["issue"] = f"{len(broken_images)} Broken Image(s)"
            result["possible_reason"] = "Invalid image path."
            result["recommendation"] = "Replace broken image URLs."
            result["developer_action"] = "Verify image assets."
            result["details"] = broken_images

            result["screenshot"] = save_screenshot(
                page,
                "broken_images_failed.png"
            )

        else:

            print("\n✅ All Images Loaded Successfully")

            result["status"] = "PASS"

            result["screenshot"] = save_screenshot(
                page,
                "broken_images_success.png"
            )

        print("========== BROKEN IMAGES TEST END ==========\n")

        return result

    except Exception as e:

        print("\n❌ BROKEN IMAGE MODULE EXCEPTION")
        print(e)

        result["status"] = "FAIL"
        result["issue"] = str(e)
        result["possible_reason"] = "Broken image test exception."
        result["recommendation"] = "Verify image loading."
        result["developer_action"] = "Review frontend assets."

        try:
            result["screenshot"] = save_screenshot(
                page,
                "broken_images_exception.png"
            )
        except:
            pass

        return result            
 
# =====================================
# Module 7
# Image Testing
# =====================================

def image_test(page, url):

    result = create_result("Images")

    try:
        
        # =====================================
        # Part 7.1
        # =====================================
        print("\n======================================")
        print("IMAGE TEST START")
        print("======================================")

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        # Collect all images

        images = page.locator("img")

        total_images = images.count()

        print(f"Total Images Found : {total_images}")

        result["total_images"] = total_images

        if total_images == 0:

            print("❌ No Images Found")

            result["status"] = "FAIL"

            result["issue"] = "No images found."

            result["possible_reason"] = "Website contains no img tags."

            result["recommendation"] = "Add website images."

            result["developer_action"] = "Verify frontend."

            result["screenshot"] = save_screenshot(
                page,
                "images_missing.png"
            )

            return result

        broken_images = []

        missing_alt = []

        hidden_images = []

        lazy_images = []

        image_details = []

        print("--------------------------------------")
        print("Starting Image Scan...")
        print("--------------------------------------")

        # =====================================
        # Part 7.2 (Loop Through Images)
        # =====================================

        for i in range(total_images):

            print("\n--------------------------------------")
            print(f"Checking Image : {i+1}/{total_images}")

            try:

                image = images.nth(i)

                src = image.get_attribute("src")
                alt = image.get_attribute("alt")
                loading = image.get_attribute("loading")

                print(f"SRC      : {src}")
                print(f"ALT      : {alt}")
                print(f"Loading  : {loading}")

                visible = image.is_visible()

                print(f"Visible  : {visible}")

                # Save details

                image_details.append({

                    "src": src,

                    "alt": alt,

                    "visible": visible,

                    "loading": loading

                })

                # -------------------------
                # Hidden Image
                # -------------------------

                if not visible:

                    print("❌ Hidden Image")

                    hidden_images.append(src)

                # -------------------------
                # Missing ALT
                # -------------------------

                if alt is None or alt.strip() == "":

                    print("❌ Missing ALT")

                    missing_alt.append(src)

                else:

                    print("✅ ALT Available")

                # -------------------------
                # Lazy Loading
                # -------------------------

                if loading == "lazy":

                    print("✅ Lazy Loading Enabled")

                    lazy_images.append(src)

                # -------------------------
                # Broken Image Check
                # -------------------------

                if src:

                    try:

                        full_url = urljoin(url, src)

                        print(f"Checking URL : {full_url}")

                        response = page.request.get(

                            full_url,

                            timeout=10000

                        )

                        print(f"HTTP Status : {response.status}")

                        if response.status >= 400:

                            print("❌ Broken Image")

                            broken_images.append({

                                "src": full_url,

                                "status": response.status

                            })

                        else:

                            print("✅ Image Working")

                    except Exception as e:

                        print("❌ Image Request Failed")

                        print(e)

                        broken_images.append({

                            "src": src,

                            "status": "No Response"

                        })

            except Exception as e:

                print("❌ Image Exception")

                print(e)

        # =====================================
        # Part 7.3
        # Image Dimension & Duplicate Check
        # =====================================

        print("\n======================================")
        print("IMAGE DIMENSION CHECK")
        print("======================================")

        duplicate_images = []
        small_images = []

        checked_src = []

        for img in image_details:

            src = img["src"]

            if not src:
                continue

            # -------------------------
            # Duplicate Image
            # -------------------------

            if src in checked_src:

                print(f"❌ Duplicate Image : {src}")

                duplicate_images.append(src)

            else:

                checked_src.append(src)

                print(f"✅ Unique Image : {src}")

            # -------------------------
            # Width / Height
            # -------------------------

            try:

                locator = page.locator(f'img[src="{src}"]').first

                width = locator.evaluate(
                    "(el)=>el.naturalWidth"
                )

                height = locator.evaluate(
                    "(el)=>el.naturalHeight"
                )

                print(f"Width  : {width}")
                print(f"Height : {height}")

                if width < 100 or height < 100:

                    print("⚠ Small Image")

                    small_images.append({

                        "src": src,

                        "width": width,

                        "height": height

                    })

                else:

                    print("✅ Image Resolution OK")

            except Exception as e:

                print("Image Dimension Error")

                print(e)

        result["duplicate_images"] = len(duplicate_images)
        result["small_images"] = len(small_images)
        result["duplicate_details"] = duplicate_images
        result["small_image_details"] = small_images

        print("\n======================================")
        print(f"Duplicate Images : {len(duplicate_images)}")
        print(f"Small Images     : {len(small_images)}")
        print("======================================")
        
        # =====================================
        # Part 7.4
        # Final Result
        # =====================================

        print("\n======================================")
        print("IMAGE TEST SUMMARY")
        print("======================================")

        print(f"Total Images      : {total_images}")
        print(f"Broken Images     : {len(broken_images)}")
        print(f"Missing ALT       : {len(missing_alt)}")
        print(f"Hidden Images     : {len(hidden_images)}")
        print(f"Lazy Loaded       : {len(lazy_images)}")
        print(f"Duplicate Images  : {len(duplicate_images)}")
        print(f"Small Images      : {len(small_images)}")

        result["broken_images"] = len(broken_images)
        result["missing_alt"] = len(missing_alt)
        result["hidden_images"] = len(hidden_images)
        result["lazy_loaded"] = len(lazy_images)

        result["broken_image_details"] = broken_images
        result["missing_alt_details"] = missing_alt
        result["hidden_image_details"] = hidden_images

        # -------------------------
        # PASS / FAIL
        # -------------------------

        if (
            broken_images or
            missing_alt or
            hidden_images
        ):

            print("\n❌ IMAGE TEST FAILED")

            result["status"] = "FAIL"

            issues = []

            if broken_images:
                issues.append(f"{len(broken_images)} Broken Images")

            if missing_alt:
                issues.append(f"{len(missing_alt)} Missing ALT")

            if hidden_images:
                issues.append(f"{len(hidden_images)} Hidden Images")

            result["issue"] = ", ".join(issues)

            result["possible_reason"] = (
                "Image loading or accessibility issue."
            )

            result["recommendation"] = (
                "Fix broken images, add ALT text and verify visibility."
            )

            result["developer_action"] = (
                "Review frontend image rendering."
            )

            result["screenshot"] = save_screenshot(
                page,
                "image_test_failed.png"
            )

        else:

            print("\n✅ IMAGE TEST PASSED")

            result["status"] = "PASS"

            result["screenshot"] = save_screenshot(
                page,
                "image_test_success.png"
            )

        print("======================================")
        print("IMAGE TEST COMPLETED")
        print("======================================")

        return result

    except Exception as e:

        print("\n❌ IMAGE MODULE EXCEPTION")
        print(e)

        result["status"] = "FAIL"

        result["issue"] = str(e)

        result["possible_reason"] = (
            "Unexpected exception during image testing."
        )

        result["recommendation"] = (
            "Verify image loading."
        )

        result["developer_action"] = (
            "Review image module."
        )

        try:

            result["screenshot"] = save_screenshot(
                page,
                "image_test_exception.png"
            )

        except:
            pass

        return result
    
# =====================================
# Module 8 : Content Validation
# Part 1 : Detect Text Elements
# =====================================
def content_validation_test(page):

    result = {

        "module": "Content Validation",
        "status": "PASS",
        "page_load_time": 0,
        "performance": "",
        "issue": "",
        "possible_reason": "",
        "recommendation": "",
        "developer_action": "",
        "screenshot": "",

        "total_text_blocks": 0,
        "text_details": [],

        "empty_text": 0,
        "empty_text_details": [],

        "lorem_ipsum": 0,
        "lorem_details": [],

        "duplicate_heading": 0,
        "duplicate_heading_details": [],

        "missing_h1": False,
        "missing_meta_description": False,

        "word_count": 0

    }

    print("\n======================================")
    print("CONTENT VALIDATION START")
    print("======================================")

    try:

        page.goto(page.url)

        page.wait_for_load_state("networkidle")

        selectors = [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "span",
            "label",
            "button",
            "a",
            "li"
        ]

        elements = []
        for selector in selectors:

            try:

                locator = page.locator(selector)

                count = locator.count()

                print(f"{selector} : {count}")

                for i in range(count):

                    text = locator.nth(i).inner_text().strip()

                    elements.append(text)

            except Exception as e:

                print(f"{selector} Error")
                print(e)

        result["total_text_blocks"] = len(elements)

        print(f"Total Text Elements : {len(elements)}")

        console_errors = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text)
                if msg.type == "error"
                else None
            )
        )

        # ======================================
        # 8.2 CSS & JavaScript Resource Test
        # ======================================

        print("\n======================================")
        print("CSS & JS RESOURCE TEST")
        print("======================================")

        css_files = page.locator("link[rel='stylesheet']").evaluate_all(
            "(els) => els.map(e => e.href)"
        )

        js_files = page.locator("script[src]").evaluate_all(
            "(els) => els.map(e => e.src)"
        )

        broken_css = 0
        broken_js = 0

        print(f"CSS Files : {len(css_files)}")
        print(f"JS Files  : {len(js_files)}")

        # ---------- CSS ----------
        for css in css_files:

            try:

                response = page.request.get(css)

                print("--------------------------------")
                print(f"CSS : {css}")
                print(f"Status : {response.status}")

                if response.status >= 400:

                    print("❌ Broken CSS")
                    broken_css += 1

                else:

                    print("✅ CSS Loaded")

            except Exception:

                print("❌ CSS Request Failed")
                broken_css += 1


        # ---------- JS ----------
        for js in js_files:

            try:

                response = page.request.get(js)

                print("--------------------------------")
                print(f"JS : {js}")
                print(f"Status : {response.status}")

                if response.status >= 400:

                    print("❌ Broken JS")
                    broken_js += 1

                else:

                    print("✅ JS Loaded")

            except Exception:

                print("❌ JS Request Failed")
                broken_js += 1


        result["css_files"] = len(css_files)
        result["js_files"] = len(js_files)
        result["broken_css"] = broken_css
        result["broken_js"] = broken_js

        print("\n======================================")
        print(f"Broken CSS : {broken_css}")
        print(f"Broken JS  : {broken_js}")
        print("======================================")

        # ======================================
        # Broken CSS / JS Summary
        # ======================================

        print("\n======================================")
        print("BROKEN CSS / JS SUMMARY")
        print("======================================")

        print(f"Total CSS Files        : {len(css_files)}")
        print(f"Broken CSS Files       : {broken_css}")

        print("\n--------------------------------------")

        print(f"Total JS Files         : {len(js_files)}")
        print(f"Broken JS Files        : {broken_js}")

        print("\n--------------------------------------")

        print(f"Console Errors         : {len(console_errors)}")

        if console_errors:
            print("\nConsole Error Details:")
            for err in console_errors:
                print(" -", err)

        print("======================================")

        # ======================================
        # Final Result
        # ======================================

        if (
            broken_css == 0
            and broken_js == 0
            and len(console_errors) == 0
        ):

            result["status"] = "PASS"

            print("✅ CSS / JS TEST PASSED")

        else:

            result["status"] = "FAIL"

            result["issue"] = (
                f"{broken_css} Broken CSS | "
                f"{broken_js} Broken JS | "
                f"{len(console_errors)} Console Errors"
            )

            result["possible_reason"] = (
                "Missing static files or frontend build issues."
            )

            result["recommendation"] = (
                "Verify CSS, JS imports and browser console."
            )

            result["developer_action"] = (
                "Fix broken assets and remove JS errors."
            )

            print("❌ CSS / JS TEST FAILED")

        print("======================================")
        print("CSS / JS TEST COMPLETED")
        print("======================================")

        return result

    except Exception as e:

        print("\n❌ CONTENT VALIDATION EXCEPTION")
        print(e)
        result["status"] = "FAIL"
        result["issue"] = str(e)
        return result


# =====================================
# Module 9 : Content Quality
# =====================================

def content_quality_test(page):

    # Initializing the dictionary with the fields you requested
    result = {
        "status": "PASS",
        "issue": "",
        "possible_reason": "",
        "recommendation": "",
        "developer_action": "",
        "desktop": {"status": ""},
        "tablet": {"status": ""},
        "mobile": {"status": "", "mobile_menu": False},
        "screenshots": [],
        "overflow_elements": 0,
        "overflow_details": [],
        "responsive_failed": 0,
        "responsive_details": [],
        "broken_content_images": 0,
        "empty_anchor_text": 0,
        "empty_anchor_details": [],
        "duplicate_paragraphs": 0,
        "duplicate_paragraph_details": [],
        "hidden_content": 0,
        "hidden_content_details": [],
        "encoding_issues": 0,
        "encoding_issue_details": []
    }

    try:

        # ======================================
        # 9.1 DESKTOP VIEW TEST
        # ======================================

        print("\n======================================")
        print("DESKTOP RESPONSIVE TEST")
        print("======================================")

        print("Setting Viewport : 1920 x 1080")

        page.set_viewport_size({
            "width": 1920,
            "height": 1080
        })

        page.reload()
        page.wait_for_load_state("networkidle")

        print("--------------------------------------")
        print("Checking Desktop Layout...")

        body_width = page.evaluate(
            "document.body.scrollWidth"
        )

        window_width = page.evaluate(
            "window.innerWidth"
        )

        print(f"Window Width : {window_width}")
        print(f"Body Width   : {body_width}")

        if body_width > window_width:

            print("❌ Horizontal Scroll Found")

            result["desktop"]["status"] = "FAIL"

            result["horizontal_scroll"] = True

        else:

            print("✅ No Horizontal Scroll")

            result["desktop"]["status"] = "PASS"

        print("--------------------------------------")

        desktop_ss = save_screenshot(
            page,
            "desktop_view.png"
        )

        print("📸 Desktop Screenshot Saved")

        result["screenshots"].append(desktop_ss)

        print("======================================")
        print("DESKTOP TEST COMPLETED")
        print("======================================")


        # ======================================
        # 9.2 TABLET VIEW TEST
        # ======================================

        print("\n======================================")
        print("TABLET RESPONSIVE TEST")
        print("======================================")

        print("Setting Viewport : 768 x 1024")

        page.set_viewport_size({
            "width": 768,
            "height": 1024
        })

        page.reload()
        page.wait_for_load_state("networkidle")

        print("--------------------------------------")
        print("Checking Tablet Layout...")

        body_width = page.evaluate(
            "document.body.scrollWidth"
        )

        window_width = page.evaluate(
            "window.innerWidth"
        )

        print(f"Window Width : {window_width}")
        print(f"Body Width   : {body_width}")

        if body_width > window_width:

            print("❌ Horizontal Scroll Found")

            result["tablet"]["status"] = "FAIL"

            result["horizontal_scroll"] = True

        else:

            print("✅ No Horizontal Scroll")

            result["tablet"]["status"] = "PASS"

        print("--------------------------------------")

        tablet_ss = save_screenshot(
            page,
            "tablet_view.png"
        )

        print("📸 Tablet Screenshot Saved")

        result["screenshots"].append(tablet_ss)

        print("======================================")
        print("TABLET TEST COMPLETED")
        print("======================================")


        # ======================================
        # 9.3 MOBILE VIEW TEST
        # ======================================

        print("\n======================================")
        print("MOBILE RESPONSIVE TEST")
        print("======================================")

        print("Setting Viewport : 375 x 812")

        page.set_viewport_size({
            "width": 375,
            "height": 812
        })

        page.reload()
        page.wait_for_load_state("networkidle")

        print("--------------------------------------")
        print("Checking Mobile Layout...")

        body_width = page.evaluate(
            "document.body.scrollWidth"
        )

        window_width = page.evaluate(
            "window.innerWidth"
        )

        print(f"Window Width : {window_width}")
        print(f"Body Width   : {body_width}")

        if body_width > window_width:

            print("❌ Horizontal Scroll Found")

            result["mobile"]["status"] = "FAIL"

            result["horizontal_scroll"] = True

        else:

            print("✅ No Horizontal Scroll")

            result["mobile"]["status"] = "PASS"

        # --------------------------------------
        # Mobile Navigation Check
        # --------------------------------------

        print("--------------------------------------")
        print("Checking Mobile Navigation...")

        menu_found = False

        menu_selectors = [
            "button[aria-label*=menu i]",
            "button[aria-label*=navigation i]",
            ".hamburger",
            ".menu-toggle",
            ".navbar-toggler",
            "#menu-toggle"
        ]

        for selector in menu_selectors:

            try:

                if page.locator(selector).count() > 0:

                    menu_found = True

                    print(f"✅ Mobile Menu Found : {selector}")

                    break

            except:
                pass

        if not menu_found:

            print("⚠ Mobile Menu Not Found")

        result["mobile"]["mobile_menu"] = menu_found

        # --------------------------------------
        # Screenshot
        # --------------------------------------

        mobile_ss = save_screenshot(
            page,
            "mobile_view.png"
        )

        print("📸 Mobile Screenshot Saved")

        result["screenshots"].append(mobile_ss)

        print("======================================")
        print("MOBILE TEST COMPLETED")
        print("======================================")


        # ======================================
        # 9.4 HORIZONTAL SCROLL TEST
        # ======================================

        print("\n======================================")
        print("HORIZONTAL SCROLL TEST")
        print("======================================")

        print("Scanning Entire Page...")

        overflow_elements = page.evaluate("""
        () => {
            let list = [];

            document.querySelectorAll("*").forEach(el => {

                if (el.scrollWidth > window.innerWidth) {

                    list.push({
                        tag: el.tagName,
                        id: el.id,
                        className: el.className,
                        width: el.scrollWidth
                    });

                }

            });

            return list;
        }
        """)

        print("--------------------------------------")

        if len(overflow_elements) == 0:

            print("✅ No Overflow Elements Found")

            result["overflow_elements"] = 0

        else:

            print(f"❌ Overflow Elements : {len(overflow_elements)}")

            result["overflow_elements"] = len(overflow_elements)

            result["overflow_details"] = overflow_elements

            for item in overflow_elements:

                print("--------------------------------")
                print(f"Tag    : {item['tag']}")
                print(f"ID     : {item['id']}")
                print(f"Class  : {item['className']}")
                print(f"Width  : {item['width']}")

        scroll_ss = save_screenshot(
            page,
            "horizontal_scroll_test.png"
        )

        print("📸 Horizontal Scroll Screenshot Saved")

        result["screenshots"].append(scroll_ss)

        print("======================================")
        print("HORIZONTAL SCROLL TEST COMPLETED")
        print("======================================")


        # ======================================
        # 9.5 RESPONSIVE ELEMENTS TEST
        # ======================================

        print("\n======================================")
        print("RESPONSIVE ELEMENTS TEST")
        print("======================================")

        responsive_failed = []
        elements = [

            ("img", "Images"),
            ("button", "Buttons"),
            ("input", "Inputs"),
            ("select", "Dropdowns"),
            ("textarea", "Textarea"),
            ("table", "Tables"),
            ("nav", "Navigation"),
            ("form", "Forms")

        ]

        for selector, name in elements:

            locator = page.locator(selector)

            count = locator.count()

            print("--------------------------------------")
            print(f"{name} Found : {count}")

            for i in range(count):

                try:

                    element = locator.nth(i)

                    visible = element.is_visible()

                    box = element.bounding_box()

                    if box:

                        width = box["width"]
                        height = box["height"]

                    else:

                        width = 0
                        height = 0

                    print(
                        f"{name} {i+1} | "
                        f"Visible={visible} | "
                        f"W={width:.0f} | "
                        f"H={height:.0f}"
                    )

                    if not visible or width <= 0 or height <= 0:

                        responsive_failed.append(
                            f"{name} {i+1}"
                        )

                except Exception:

                    responsive_failed.append(
                        f"{name} {i+1}"
                    )

        result["responsive_failed"] = len(responsive_failed)
        result["responsive_details"] = responsive_failed

        responsive_ss = save_screenshot(
            page,
            "responsive_elements_test.png"
        )

        result["screenshots"].append(responsive_ss)

        print("--------------------------------------")
        print(f"Responsive Failed : {len(responsive_failed)}")

        if responsive_failed:

            print("\nFailed Elements:")

            for item in responsive_failed:

                print(" -", item)

        print("======================================")
        print("RESPONSIVE ELEMENT TEST COMPLETED")
        print("======================================")


        # ======================================
        # 9.6 Broken Images Inside Content
        # ======================================

        print("\n======================================")
        print("BROKEN CONTENT IMAGES TEST")
        print("======================================")

        content_images = page.locator("article img, main img, section img").all()

        broken_content_images = []

        print(f"Images Inside Content : {len(content_images)}")

        for i, img in enumerate(content_images, start=1):

            print("--------------------------------")
            print(f"Checking Image {i}")

            try:

                src = img.get_attribute("src")

                print(f"SRC : {src}")

                if src:

                    response = page.request.get(src)

                    print(f"Status : {response.status}")

                    if response.status >= 400:

                        print("❌ Broken Content Image")

                        broken_content_images.append(src)

                    else:

                        print("✅ Image Working")

            except Exception:

                print("❌ Image Request Failed")

                broken_content_images.append(src)

        result["broken_content_images"] = len(broken_content_images)

        print("\n======================================")
        print(f"Broken Content Images : {len(broken_content_images)}")
        print("======================================")


        # ======================================
        # 9.7 EMPTY ANCHOR TEXT TEST
        # ======================================

        print("\n======================================")
        print("EMPTY ANCHOR TEXT TEST")
        print("======================================")

        anchors = page.locator("a").all()
        empty_links = []
        print(f"Total Anchor Tags : {len(anchors)}")

        for i, anchor in enumerate(anchors, start=1):

            print("--------------------------------")
            print(f"Checking Anchor : {i}")

            try:

                text = anchor.inner_text().strip()

                href = anchor.get_attribute("href")

                print(f"Text : {text}")
                print(f"Href : {href}")

                if text == "":

                    print("❌ Empty Anchor Text")

                    empty_links.append({

                        "href": href

                    })

                else:

                    print("✅ Anchor Text Available")

            except Exception as e:

                print("❌ Error")

                print(e)

        result["empty_anchor_text"] = len(empty_links)
        result["empty_anchor_details"] = empty_links

        print("\n======================================")
        print(f"Empty Anchor Text : {len(empty_links)}")
        print("======================================")


        # ======================================
        # 9.8 DUPLICATE PARAGRAPH TEST
        # ======================================

        print("\n======================================")
        print("DUPLICATE PARAGRAPH TEST")
        print("======================================")

        paragraphs = page.locator("p").all()

        duplicate_paragraphs = []

        all_text = []

        print(f"Total Paragraphs : {len(paragraphs)}")

        for i, para in enumerate(paragraphs, start=1):

            print("--------------------------------")
            print(f"Checking Paragraph : {i}")

            try:

                text = para.inner_text().strip()

                print(f"Length : {len(text)}")

                if text == "":

                    print("⚠ Empty Paragraph")
                    continue

                if text in all_text:

                    print("❌ Duplicate Paragraph Found")

                    duplicate_paragraphs.append({

                        "paragraph_no": i,

                        "text": text[:100]

                    })

                else:

                    print("✅ Unique Paragraph")

                    all_text.append(text)

            except Exception as e:

                print("❌ Error")
                print(e)

        result["duplicate_paragraphs"] = len(duplicate_paragraphs)

        result["duplicate_paragraph_details"] = duplicate_paragraphs

        print("\n======================================")
        print(f"Duplicate Paragraphs : {len(duplicate_paragraphs)}")
        print("======================================")


        # ======================================
        # 9.9 HIDDEN CONTENT TEST
        # ======================================

        print("\n======================================")
        print("HIDDEN CONTENT TEST")
        print("======================================")

        hidden_elements = []
        elements = page.locator("*").all()
        print(f"Total Elements : {len(elements)}")

        for i, element in enumerate(elements, start=1):

            try:

                tag = element.evaluate(
                    "el => el.tagName"
                )

                visible = element.is_visible()

                print("--------------------------------")
                print(f"Element : {i}")
                print(f"Tag     : {tag}")
                print(f"Visible : {visible}")

                if not visible:

                    print("❌ Hidden Element")

                    hidden_elements.append({

                        "tag": tag,

                        "index": i

                    })

                else:

                    print("✅ Visible")

            except Exception:

                pass

        result["hidden_content"] = len(hidden_elements)
        result["hidden_content_details"] = hidden_elements

        print("\n======================================")
        print(f"Hidden Elements : {len(hidden_elements)}")

        if hidden_elements:

            print("\nHidden Elements List")

            for item in hidden_elements:

                print(
                    f"Tag : {item['tag']} | "
                    f"Index : {item['index']}"
                )

        print("======================================")
        print("HIDDEN CONTENT TEST COMPLETED")
        print("======================================")


        # ======================================
        # 9.10 SPECIAL CHARACTER TEST
        # ======================================

        print("\n======================================")
        print("SPECIAL CHARACTER TEST")
        print("======================================")

        encoding_issues = []
        page_text = page.locator("body").inner_text()
        special_patterns = [

            "",
            "&nbsp;",
            "&amp;",
            "&#39;",
            "&lt;",
            "&gt;"

        ]

        print(f"Scanning {len(special_patterns)} Patterns...")

        for pattern in special_patterns:

            print("--------------------------------")
            print(f"Checking : {pattern}")

            if pattern in page_text:

                print("❌ Found")

                encoding_issues.append(pattern)

            else:

                print("✅ Not Found")

        result["encoding_issues"] = len(encoding_issues)
        result["encoding_issue_details"] = encoding_issues

        print("\n======================================")
        print(f"Encoding Issues : {len(encoding_issues)}")

        if encoding_issues:

            print("\nDetected Issues")

            for issue in encoding_issues:

                print(f" - {issue}")

        print("======================================")

        if len(encoding_issues) == 0:

            print("✅ SPECIAL CHARACTER TEST PASSED")

        else:

            result["status"] = "FAIL"

            result["issue"] = (
                f"{len(encoding_issues)} Encoding Issues Found"
            )

            result["possible_reason"] = (
                "HTML Encoding / Unicode issue."
            )

            result["recommendation"] = (
                "Replace encoded characters with proper UTF-8 text."
            )

            result["developer_action"] = (
                "Review frontend rendering and encoding."
            )

            print("❌ SPECIAL CHARACTER TEST FAILED")

        print("======================================")
        print("SPECIAL CHARACTER TEST COMPLETED")
        print("======================================")

        return result

    except Exception as e:
        
        print("\n❌ CONTENT QUALITY TEST EXCEPTION")
        print(e)

        result["status"] = "FAIL"
        result["issue"] = str(e)
        
        return result
    
# ======================================
# MODULE 11 : SESSION & COOKIES TEST
# ======================================

def session_cookie_test(page):

    result = {
        "module": "Session & Cookies",
        "status": "PASS",
        "total_cookies": 0,
        "session_cookie_found": False,
        "secure_cookie": 0,
        "http_only_cookie": 0,
        "same_site_cookie": 0,
        "issues": [],
        "screenshots": []
    }

    try:

        print("\n======================================")
        print("SESSION & COOKIES TEST")
        print("======================================")

        cookies = page.context.cookies()

        result["total_cookies"] = len(cookies)

        print(f"Total Cookies : {len(cookies)}")

        for cookie in cookies:

            print("--------------------------------------")
            print(f"Name : {cookie['name']}")

            session_keywords = [
                "session",
                "sess",
                "sid",
                "auth",
                "token",
                "jwt",
                "__session",
                "__secure",
                "__host"
                ""
            ]

            name = cookie["name"].lower()

            if any(k in name for k in session_keywords):
                result["session_cookie_found"] = True

            if cookie.get("secure"):
                result["secure_cookie"] += 1

            if cookie.get("httpOnly"):
                result["http_only_cookie"] += 1

            if cookie.get("sameSite"):
                result["same_site_cookie"] += 1

        print("--------------------------------------")

        if result["total_cookies"] == 0:
            result["issues"].append("No Cookies Found")

        if result["secure_cookie"] == 0:
            result["issues"].append("Secure Cookie Missing")

        if result["http_only_cookie"] == 0:
            result["issues"].append("HttpOnly Cookie Missing")

        if result["same_site_cookie"] == 0:
            result["issues"].append("SameSite Cookie Missing")

        if len(result["issues"]) > 0:

            result["status"] = "FAIL"

            print("❌ Issues Found")

            for issue in result["issues"]:
                print("-", issue)

        else:

            print("✅ Session Cookies Valid")

        ss = save_screenshot(
            page,
            "session_cookie_test.png"
        )

        result["screenshots"].append(ss)

        print("======================================")
        print("SESSION & COOKIES TEST COMPLETED")
        print("======================================")

        return result

    except Exception as e:

        result["status"] = "FAIL"

        result["issues"].append(str(e))

        print(e)

        return result
    
# ======================================
# MODULE 12 : SEARCH FUNCTIONALITY
# ======================================

def search_functionality_test(page):

    result = {
        "module": "Search Functionality",
        "status": "PASS",
        "search_box_found": False,
        "search_button_found": False,
        "search_working": False,
        "results_found": 0,
        "issues": [],
        "screenshots": []
    }

    try:

        print("\n======================================")
        print("SEARCH FUNCTIONALITY TEST")
        print("======================================")

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        # -------------------------------
        # Detect Search Box
        # -------------------------------

        search_box = page.locator("""
            input[type='search'],
            input[placeholder*='Search' i],
            input[name*='search' i],
            input[id*='search' i]
        """).first

        if search_box.count() == 0:

            result["status"] = "SKIPPED"
            result["issues"].append("Search Feature Not Available")

            ss = save_screenshot(
                page,
                "search_not_available.png"
            )

            result["screenshots"].append(ss)

            print("Search Feature Not Found")

            return result

        result["search_box_found"] = True

        print("Search Box Found")

        # -------------------------------
        # Detect Search Button
        # -------------------------------

        search_button = page.locator("""
            button[type='submit'],
            button[aria-label*='search' i],
            button:has-text('Search'),
            svg
        """).first

        if search_button.count() > 0:

            result["search_button_found"] = True

            print("Search Button Found")

        # -------------------------------
        # Search Test
        # -------------------------------

        test_keyword = "test"

        print(f"Searching : {test_keyword}")

        search_box.fill(test_keyword)

        if result["search_button_found"]:

            search_button.click(force=True)

        else:

            search_box.press("Enter")

        page.wait_for_timeout(4000)

        # -------------------------------
        # Detect Results
        # -------------------------------

        results = page.locator("""
            .result,
            .results,
            .search-result,
            article,
            .card,
            li
        """)

        total = results.count()

        result["results_found"] = total

        if total > 0:

            result["search_working"] = True

            print(f"Results Found : {total}")

        else:

            print("No Search Results Found")

            no_result = page.locator(
                "text=/no results|not found|nothing found/i"
            )

            if no_result.count() == 0:

                result["status"] = "FAIL"

                result["issues"].append(
                    "Search did not return results"
                )

        ss = save_screenshot(
            page,
            "search_test.png"
        )

        result["screenshots"].append(ss)

        print("======================================")
        print("SEARCH TEST COMPLETED")
        print("======================================")

        return result

    except Exception as e:

        result["status"] = "FAIL"

        result["issues"].append(str(e))

        try:

            ss = save_screenshot(
                page,
                "search_exception.png"
            )

            result["screenshots"].append(ss)

        except:
            pass

        return result  
   
# ======================================
# MODULE 13 : ACCESSIBILITY (WCAG)
# Part 1
# ======================================

from bs4 import BeautifulSoup


def accessibility_check(page):

    result = {
        "module": "Accessibility (WCAG)",
        "status": "PASS",

        "accessibility_score": 100,

        "total_images": 0,
        "images_without_alt": 0,

        "total_buttons": 0,
        "buttons_without_text": 0,

        "total_inputs": 0,
        "inputs_without_label": 0,

        "missing_h1": False,
        "missing_page_title": False,
        "missing_lang_attribute": False,

        "empty_links": 0,
        "duplicate_ids": 0,

        "issues": [],
        "recommendations": [],

        "screenshots": []
    }

    try:

        print("\n======================================")
        print("ACCESSIBILITY (WCAG) TEST")
        print("======================================")

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        screenshot = save_screenshot(
            page,
            "accessibility_test.png"
        )

        result["screenshots"].append(
            screenshot
        )

        html = page.content()

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # ----------------------------------
        # Collect Elements
        # ----------------------------------

        images = soup.find_all("img")

        buttons = soup.find_all("button")

        inputs = soup.find_all("input")

        labels = soup.find_all("label")

        links = soup.find_all("a")

        headings = soup.find_all("h1")

        result["total_images"] = len(images)

        result["total_buttons"] = len(buttons)

        result["total_inputs"] = len(inputs)

        print(f"Images   : {len(images)}")
        print(f"Buttons  : {len(buttons)}")
        print(f"Inputs   : {len(inputs)}")
        print(f"H1 Tags  : {len(headings)}")

        images_without_alt = 0
        buttons_without_text = 0
        inputs_without_label = 0
        empty_links = 0
        duplicate_ids = 0
        
       # ======================================
        # 13.1 IMAGE ALT CHECK
        # ======================================

        print("\n--------------------------------------")
        print("IMAGE ALT CHECK")
        print("--------------------------------------")

        for img in images:

            src = img.get("src", "")

            # Ignore tracking / analytics images
            if (
                "facebook.com/tr" in src
                or "adsct" in src
                or "analytics.twitter.com" in src
                or "doubleclick" in src
                or "googleads" in src
                or src.startswith("data:")
            ):
                continue

            print(f"Image : {src}")

            if not img.get("alt") or img.get("alt").strip() == "":

                images_without_alt += 1

                result["issues"].append(
                    f"Missing ALT : {src}"
                )
                
                print("❌ ALT Missing")

            else:

                print("✅ ALT Available")

        # ======================================
        # 13.2 BUTTON TEXT CHECK
        # ======================================

        print("\n--------------------------------------")
        print("BUTTON ACCESSIBILITY")
        print("--------------------------------------")

        for btn in buttons:

            text = btn.get_text(strip=True)

            aria = btn.get("aria-label")

            if text == "" and not aria:

                buttons_without_text += 1

                result["issues"].append(
                    "Button missing text/aria-label"
                )

                print("❌ Button Missing Text")

            else:

                print("✅ Button Accessible")


        # ======================================
        # 13.3 INPUT LABEL CHECK
        # ======================================

        print("\n--------------------------------------")
        print("INPUT LABEL CHECK")
        print("--------------------------------------")

        for field in inputs:

            field_id = field.get("id")

            placeholder = field.get("placeholder")

            aria = field.get("aria-label")

            has_label = False

            if field_id:

                lbl = soup.find(
                    "label",
                    attrs={"for": field_id}
                )

                if lbl:
                    has_label = True

            if not has_label and not placeholder and not aria:

                inputs_without_label += 1

                result["issues"].append(
                    f"Input missing label : {field.get('name')}"
                )

                print("❌ Input Missing Label")

            else:

                print("✅ Input Accessible")


        # ======================================
        # 13.4 EMPTY LINKS
        # ======================================

        print("\n--------------------------------------")
        print("EMPTY LINK CHECK")
        print("--------------------------------------")

        for link in links:

            href = link.get("href", "")

            text = link.get_text(strip=True)

            aria = link.get("aria-label")

            title = link.get("title")

            img = link.find("img")

            svg = link.find("svg")

            # Ignore navigation links
            if href in [
                "/",
                "/home",
                "/settings",
                "#"
            ]:
                continue

            if img or svg:
                continue

            if not text and not aria and not title:

                empty_links += 1

                result["issues"].append(
                    f"Empty Link : {href}"
                )

                print("❌ Empty Link")

            else:

                print("✅ Link Accessible")


        # ======================================
        # 13.5 DUPLICATE IDS
        # ======================================

        print("\n--------------------------------------")
        print("DUPLICATE ID CHECK")
        print("--------------------------------------")

        ids = []

        for tag in soup.find_all(True):

            tag_id = tag.get("id")

            if not tag_id:
                continue

            if tag_id in ids:

                duplicate_ids += 1

                result["issues"].append(
                    f"Duplicate ID : {tag_id}"
                )

                print(f"❌ Duplicate ID : {tag_id}")

            else:

                ids.append(tag_id)

        if duplicate_ids == 0:

            print("✅ No Duplicate IDs")


        # ======================================
        # 13.6 H1 CHECK
        # ======================================

        if len(headings) != 1:

            result["missing_h1"] = True

            result["issues"].append(
                "Page should contain exactly one H1"
            )

            print("❌ H1 Issue")

        else:

            print("✅ H1 Present")


        # ======================================
        # 13.7 PAGE TITLE
        # ======================================

        title = page.title().strip()

        if title == "":

            result["missing_page_title"] = True

            result["issues"].append(
                "Page title missing"
            )

            print("❌ Title Missing")

        else:

            print(f"✅ Title : {title}")


        # ======================================
        # 13.8 HTML LANG CHECK
        # ======================================

        html_tag = soup.find("html")

        if html_tag is None or not html_tag.get("lang"):

            result["missing_lang_attribute"] = True

            result["issues"].append(
                "HTML lang attribute missing"
            )

            print("❌ Lang Attribute Missing")

        else:

            print(
                f"✅ Lang : {html_tag.get('lang')}"
            )

        # ======================================
        # 13.9 SCORE CALCULATION
        # ======================================

        print("\n======================================")
        print("ACCESSIBILITY SCORE")
        print("======================================")

        score = 100

        score -= images_without_alt * 3
        score -= buttons_without_text * 10
        score -= inputs_without_label * 5
        score -= empty_links * 2
        score -= duplicate_ids * 5

        if result["missing_h1"]:
            score -= 5

        if result["missing_page_title"]:
            score -= 5

        if result["missing_lang_attribute"]:
            score -= 5

        if score < 0:
            score = 0

        result["accessibility_score"] = score

        result["images_without_alt"] = images_without_alt
        result["buttons_without_text"] = buttons_without_text
        result["inputs_without_label"] = inputs_without_label
        result["empty_links"] = empty_links
        result["duplicate_ids"] = duplicate_ids

        print(f"Accessibility Score : {score}%")

        # ======================================
        # 13.10 RECOMMENDATIONS
        # ======================================

        if images_without_alt > 0:
            result["recommendations"].append(
                "Add descriptive ALT text for every image."
            )

        if buttons_without_text > 0:
            result["recommendations"].append(
                "Provide visible text or aria-label for buttons."
            )

        if inputs_without_label > 0:
            result["recommendations"].append(
                "Associate every input with a label or aria-label."
            )

        if empty_links > 0:
            result["recommendations"].append(
                "Provide accessible text for hyperlinks."
            )

        if duplicate_ids > 0:
            result["recommendations"].append(
                "Remove duplicate HTML IDs."
            )

        if result["missing_h1"]:
            result["recommendations"].append(
                "Use exactly one H1 heading."
            )

        if result["missing_page_title"]:
            result["recommendations"].append(
                "Provide a meaningful page title."
            )

        if result["missing_lang_attribute"]:
            result["recommendations"].append(
                "Add the HTML lang attribute."
            )

        # ======================================
        # 13.11 FINAL STATUS
        # ======================================

        if len(result["issues"]) > 0:

            result["status"] = "FAIL"

            result["issue"] = (
                f"{len(result['issues'])} accessibility issue(s) found."
            )

            result["possible_reason"] = (
                "Website does not fully follow WCAG accessibility guidelines."
            )

            result["developer_action"] = (
                "Review accessibility issues and update frontend accordingly."
            )

            print("\n❌ ACCESSIBILITY TEST FAILED")

        else:

            result["status"] = "PASS"

            result["recommendations"].append(
                "No accessibility issues detected."
            )

            print("\n✅ ACCESSIBILITY TEST PASSED")

        print("======================================")
        print("ACCESSIBILITY TEST COMPLETED")
        print("======================================")

        return result

    except Exception as e:

        print("\n❌ ACCESSIBILITY MODULE EXCEPTION")
        print(e)

        result["status"] = "FAIL"

        result["issue"] = str(e)

        result["possible_reason"] = (
            "Unexpected exception while testing accessibility."
        )

        result["developer_action"] = (
            "Review accessibility module."
        )

        return result   
    
      

# =====================================
# Main Functional Testing
# =====================================

def functional_testing(url):

    results = []

    print("\n===========================================")
    print("STARTING FUNCTIONAL TEST")
    print("===========================================\n")

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            # ---------------------------
            # Module 1
            # ---------------------------

            print("\nRunning Module 1 : Website Open")

            results.append(
                website_open_test(page, url)
            )

            # ---------------------------
            # Module 2
            # ---------------------------

            print("\nRunning Module 2 : Navigation Links")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                navigation_links_test(page, url)
            )

            # ---------------------------
            # Module 3
            # ---------------------------

            print("\nRunning Module 3 : Navbar")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                navbar_test(page)
            )

            # ---------------------------
            # Module 4
            # ---------------------------

            print("\nRunning Module 4 : Footer")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                footer_test(page, url)
            )

            # ---------------------------
            # Module 5
            # ---------------------------

            print("\nRunning Module 5 : Buttons")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                buttons_test(page)
            )
            # ---------------------------
            # Module 6
            # ---------------------------

            print("\nRunning Module 6 : Forms Validation")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                form_validation_test(page)
            )
            # ---------------------------
            # Module 7
            # ---------------------------

            print("\nRunning Module 7 : Images")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                image_test(page, url)
            )
            # ---------------------------
            # Module 8
            # ---------------------------

            print("\nRunning Module 8 : Content Validation")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                content_validation_test(page)
            )
            # ---------------------------
            # Module 9
            # ---------------------------

            print("\nRunning Module 9 : Content Quality")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                content_quality_test(page)
            )
            # ---------------------------
            # Module 11
            # ---------------------------

            print("\nRunning Module 11 : Session & Cookies")

            results.append(
                session_cookie_test(page)
            )
            # ---------------------------
            # Module 12
            # ---------------------------

            print("\nRunning Module 12 : Search Functionality")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                search_functionality_test(page)
            )
            # ---------------------------
            # Module 13
            # ---------------------------

            print("\nRunning Module 13 : Accessibility (WCAG)")

            page.goto(url)

            page.wait_for_load_state("networkidle")

            results.append(
                accessibility_check(page)
            )
        
            

            browser.close()

        passed = len(
            [r for r in results if r["status"] == "PASS"]
        )

        failed = len(
            [r for r in results if r["status"] == "FAIL"]
        )

        score = int(
            (passed / len(results)) * 100
        )

        print("\n===========================================")
        print("FUNCTIONAL TEST COMPLETED")
        print("===========================================")
        print(f"Passed : {passed}")
        print(f"Failed : {failed}")
        print(f"Score  : {score}%")
        print("===========================================\n")

        return {

            "functional_score": score,

            "passed": passed,

            "failed": failed,

            "results": results

        }

    except Exception as e:

        print("\nCritical Error")
        print(e)

        return {

            "functional_score": 0,

            "passed": 0,

            "failed": 1,

            "results": [

                {

                    "module": "Functional Testing",

                    "status": "FAIL",

                    "issue": str(e),

                    "possible_reason": "Playwright Error",

                    "recommendation": "Verify Website",

                    "developer_action": "Review Logs",

                    "screenshot": ""

                }

            ]

        }    
