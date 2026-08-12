"""
PDF report generators used by the plan-tier endpoints (app/routers/plans.py).

Kept separate from app/services/pdf_service.py (which powers the legacy
/website/report and /report endpoints) so that Basic/Standard reports only
ever show the checks that actually ran for that tier - no "0 broken links /
100 security score" sections implying a check happened when it didn't.
"""

from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from app.services.pdf_service import create_styles, get_grade, add_page_number


def _status_line(label, score):
    grade = get_grade(score)
    return f"<b>{label} :</b> {score}/100 (Grade {grade})"


_DETAIL_LIST_KEYS = [
    "details",
    "issues",
    "failed_items",
    "failed_links",
    "failed_buttons",
    "broken_links",
    "broken_image_details",
    "duplicate_details",
    "hidden_image_details",
    "small_image_details",
    "missing_alt_details",
]


def _extract_failure_details(result, limit=10):
    """
    Pull the concrete failing items (e.g. which link/button/image) out of a
    module result, instead of just the one-line summary in "issue". Each
    test module names its detail list differently, so we check every field
    name that's actually used across the functional test modules.
    """

    items = []

    for key in _DETAIL_LIST_KEYS:

        value = result.get(key)

        if not isinstance(value, list) or not value:
            continue

        for entry in value:

            if isinstance(entry, dict):

                target = (
                    entry.get("url")
                    or entry.get("link")
                    or entry.get("src")
                    or entry.get("element")
                    or entry.get("selector")
                )

                reason = (
                    entry.get("status")
                    or entry.get("reason")
                    or entry.get("error")
                )

                if target:
                    text = str(target)
                    if reason:
                        text += f" ({reason})"
                elif entry:
                    text = ", ".join(
                        f"{k}: {v}" for k, v in entry.items()
                    )
                else:
                    continue

            else:
                text = str(entry)

            items.append(text)

    seen = set()
    unique_items = []

    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)

    return unique_items[:limit], len(unique_items)


def _issues_block(title, issues, normal_style):
    story = [Paragraph(f"<b>{title}</b>", normal_style)]

    if not issues:
        story.append(Paragraph("No issues detected.", normal_style))
    else:
        for issue in issues:
            story.append(Paragraph(f"&bull; {issue}", normal_style))

    story.append(Spacer(1, 0.15 * inch))
    return story


def generate_basic_pdf_report(data, filename="Basic_Website_Report.pdf"):
    """
    data keys expected: url, website (test_website result), seo, performance,
    accessibility, content_validation, image_validation
    """

    doc = SimpleDocTemplate(filename)
    styles = create_styles()
    title, heading, normal = styles["title"], styles["heading"], styles["normal"]

    story = []

    website = data.get("website", {})
    seo = data.get("seo", {})
    performance = data.get("performance", {})
    accessibility = data.get("accessibility", {})
    content = data.get("content_validation", {})
    image = data.get("image_validation", {})

    header = Table(
        [[Paragraph("<b>TESTPILOT AI</b><br/>Basic Plan Website Report", title)]],
        colWidths=[450],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF2F8")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1F4E79")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 0.3 * inch))

    story.append(
        Paragraph(
            f"<b>Website URL :</b> {data.get('url', '')}<br/>"
            f"<b>Generated :</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}<br/>"
            f"<b>Plan :</b> Basic",
            normal,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Summary Scores", heading))
    story.append(
        Paragraph(
            f"<b>Availability :</b> {website.get('test_status', 'Unknown')} "
            f"(HTTP {website.get('status_code', 'N/A')})<br/>"
            f"{_status_line('SEO Score', seo.get('seo_score', 0))}<br/>"
            f"{_status_line('Performance Score', performance.get('performance_score', 0))}<br/>"
            f"{_status_line('Accessibility Score', accessibility.get('accessibility_score', 0))}<br/>"
            f"{_status_line('Content Score', content.get('content_score', 0))}<br/>"
            f"{_status_line('Image Score', image.get('image_score', 0))}",
            normal,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Basic SEO Findings", heading))
    story.extend(_issues_block("SEO Issues", seo.get("issues", []), normal))

    story.append(Paragraph("Basic Accessibility Findings", heading))
    story.extend(
        _issues_block("Accessibility Issues", accessibility.get("issues", []), normal)
    )

    story.append(Paragraph("Basic Performance Findings", heading))
    story.extend(
        _issues_block("Performance Issues", performance.get("issues", []), normal)
    )

    story.append(Paragraph("Basic Content Validation", heading))
    story.extend(_issues_block("Content Issues", content.get("issues", []), normal))

    story.append(Paragraph("Basic Image Validation", heading))
    story.extend(_issues_block("Image Issues", image.get("issues", []), normal))

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "Upgrade to the Standard plan for functional testing, advanced SEO, "
            "advanced accessibility, API validation and AI-powered recommendations. "
            "Upgrade to Premium for a full security audit.",
            normal,
        )
    )

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    return filename


def generate_premium_pdf_report(data, filename="Premium_Website_Report.pdf"):
    """
    Premium report = everything in the Standard report (functional testing,
    advanced SEO, advanced accessibility, performance, AI recommendations)
    PLUS a Security Audit section, in a single combined PDF.

    data keys expected: url, website, seo (advanced), accessibility, performance,
    functional, ai_suggestions, security (security_testing.security_audit result)
    """

    doc = SimpleDocTemplate(filename)
    styles = create_styles()
    title, heading, normal = styles["title"], styles["heading"], styles["normal"]

    story = []

    website = data.get("website", {})
    seo = data.get("seo", {})
    performance = data.get("performance", {})
    accessibility = data.get("accessibility", {})
    functional = data.get("functional", {})
    ai_suggestions = data.get("ai_suggestions", "")
    security = data.get("security", {})

    header = Table(
        [[Paragraph("<b>TESTPILOT AI</b><br/>Premium Plan Full Report", title)]],
        colWidths=[450],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF2F8")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1F4E79")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 0.3 * inch))

    story.append(
        Paragraph(
            f"<b>Website URL :</b> {data.get('url', '')}<br/>"
            f"<b>Generated :</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}<br/>"
            f"<b>Plan :</b> Premium",
            normal,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Summary Scores", heading))
    story.append(
        Paragraph(
            f"<b>Website Health :</b> {website.get('health_score', 0)}/100<br/>"
            f"{_status_line('Advanced SEO Score', seo.get('seo_score', 0))}<br/>"
            f"{_status_line('Accessibility Score', accessibility.get('accessibility_score', 0))}<br/>"
            f"{_status_line('Performance Score', performance.get('performance_score', 0))}<br/>"
            f"{_status_line('Functional Score', functional.get('functional_score', 0))}<br/>"
            f"{_status_line('Security Score', security.get('security_score', 0))}",
            normal,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    # ---------------- STANDARD SECTION: FUNCTIONAL TESTING ----------------
    tested_modules = functional.get(
        "tested_modules",
        functional.get("passed", 0) + functional.get("failed", 0),
    )

    story.append(Paragraph("Functional Testing Summary", heading))
    story.append(
        Paragraph(
            f"<b>Modules Executed :</b> {tested_modules} / "
            f"{functional.get('total_modules', 0)}<br/>"
            f"<b>Passed :</b> {functional.get('passed', 0)} &nbsp;&nbsp;"
            f"<b>Failed :</b> {functional.get('failed', 0)} &nbsp;&nbsp;"
            f"<b>Partial :</b> {functional.get('partial', 0)} &nbsp;&nbsp;"
            f"<b>Skipped :</b> {functional.get('skipped', 0)}<br/><br/>"
            "Covers: navigation &amp; link testing, forms &amp; validation, "
            "authentication testing, responsive testing, browser compatibility, "
            "broken resource testing, console error detection and API validation.",
            normal,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    for module_result in functional.get("results", []):
        module_name = module_result.get("module", "Module")
        status = module_result.get("status", "N/A")
        story.append(Paragraph(f"&bull; <b>{module_name}</b>: {status}", normal))

        if status == "FAIL":

            issue_summary = module_result.get("issue")
            if issue_summary:
                story.append(
                    Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{issue_summary}", normal)
                )

            detail_items, total_found = _extract_failure_details(module_result)

            for item in detail_items:
                story.append(
                    Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;- {item}", normal)
                )

            if total_found > len(detail_items):
                remaining = total_found - len(detail_items)
                story.append(
                    Paragraph(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;...and {remaining} more.",
                        normal,
                    )
                )

    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("AI Recommendations", heading))
    story.append(Paragraph(str(ai_suggestions) or "No AI suggestions generated.", normal))
    story.append(Spacer(1, 0.25 * inch))

    # ---------------- PREMIUM SECTION: SECURITY AUDIT ----------------
    story.append(Paragraph("Security Audit", heading))

    severity_summary = security.get("summary", {})
    story.append(
        Paragraph(
            f"<b>Status :</b> {security.get('status', 'N/A')}<br/>"
            f"<b>Total Checks :</b> {severity_summary.get('total_checks', 0)} &nbsp;&nbsp;"
            f"<b>Passed :</b> {severity_summary.get('passed_checks', 0)} &nbsp;&nbsp;"
            f"<b>Failed :</b> {severity_summary.get('failed_checks', 0)}<br/>"
            f"<b>Critical :</b> {severity_summary.get('critical', 0)} &nbsp;&nbsp;"
            f"<b>High :</b> {severity_summary.get('high', 0)} &nbsp;&nbsp;"
            f"<b>Medium :</b> {severity_summary.get('medium', 0)} &nbsp;&nbsp;"
            f"<b>Low :</b> {severity_summary.get('low', 0)}<br/><br/>"
            "Covers: SSL/TLS audit, SSL certificate validation, TLS cipher "
            "analysis, security headers, cookie security, CORS, HTTP/HTTPS "
            "audit, HTTP methods, sensitive paths, mixed content, "
            "cache-control and information disclosure.",
            normal,
        )
    )
    story.append(Spacer(1, 0.15 * inch))

    security_issues = security.get("issues", [])
    if not security_issues:
        story.append(Paragraph("No security issues detected.", normal))
    else:
        for issue in security_issues[:15]:
            story.append(
                Paragraph(
                    f"&bull; <b>[{issue.get('severity', 'N/A')}] "
                    f"{issue.get('title', 'Issue')}</b><br/>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;{issue.get('details', '')}<br/>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;<i>Fix:</i> {issue.get('recommendation', '')}",
                    normal,
                )
            )
            story.append(Spacer(1, 0.08 * inch))

        remaining = len(security_issues) - 15
        if remaining > 0:
            story.append(
                Paragraph(
                    f"...and {remaining} more security issues. See the full "
                    "security audit JSON/PDF for details.",
                    normal,
                )
            )

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    return filename


def generate_standard_pdf_report(data, filename="Standard_Website_Report.pdf"):
    """
    data keys expected: url, website, seo (advanced), accessibility, performance,
    functional (functional_testing_service.functional_testing result),
    ai_suggestions
    """

    doc = SimpleDocTemplate(filename)
    styles = create_styles()
    title, heading, normal = styles["title"], styles["heading"], styles["normal"]

    story = []

    website = data.get("website", {})
    seo = data.get("seo", {})
    performance = data.get("performance", {})
    accessibility = data.get("accessibility", {})
    functional = data.get("functional", {})
    ai_suggestions = data.get("ai_suggestions", "")

    header = Table(
        [[Paragraph("<b>TESTPILOT AI</b><br/>Standard Plan Detailed Report", title)]],
        colWidths=[450],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF2F8")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1F4E79")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 0.3 * inch))

    story.append(
        Paragraph(
            f"<b>Website URL :</b> {data.get('url', '')}<br/>"
            f"<b>Generated :</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}<br/>"
            f"<b>Plan :</b> Standard",
            normal,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Summary Scores", heading))
    story.append(
        Paragraph(
            f"<b>Website Health :</b> {website.get('health_score', 0)}/100<br/>"
            f"{_status_line('Advanced SEO Score', seo.get('seo_score', 0))}<br/>"
            f"{_status_line('Accessibility Score', accessibility.get('accessibility_score', 0))}<br/>"
            f"{_status_line('Performance Score', performance.get('performance_score', 0))}<br/>"
            f"{_status_line('Functional Score', functional.get('functional_score', 0))}",
            normal,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    tested_modules = functional.get(
        "tested_modules",
        functional.get("passed", 0) + functional.get("failed", 0),
    )

    story.append(Paragraph("Functional Testing Summary", heading))
    story.append(
        Paragraph(
            f"<b>Modules Executed :</b> {tested_modules} / "
            f"{functional.get('total_modules', 0)}<br/>"
            f"<b>Passed :</b> {functional.get('passed', 0)} &nbsp;&nbsp;"
            f"<b>Failed :</b> {functional.get('failed', 0)} &nbsp;&nbsp;"
            f"<b>Partial :</b> {functional.get('partial', 0)} &nbsp;&nbsp;"
            f"<b>Skipped :</b> {functional.get('skipped', 0)}<br/><br/>"
            "Covers: navigation &amp; link testing, forms &amp; validation, "
            "authentication testing, responsive testing, browser compatibility, "
            "broken resource testing, console error detection and API validation.",
            normal,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    for module_result in functional.get("results", []):
        module_name = module_result.get("module", "Module")
        status = module_result.get("status", "N/A")
        story.append(Paragraph(f"&bull; <b>{module_name}</b>: {status}", normal))

        if status == "FAIL":

            issue_summary = module_result.get("issue")
            if issue_summary:
                story.append(
                    Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{issue_summary}", normal)
                )

            detail_items, total_found = _extract_failure_details(module_result)

            for item in detail_items:
                story.append(
                    Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;- {item}", normal)
                )

            if total_found > len(detail_items):
                remaining = total_found - len(detail_items)
                story.append(
                    Paragraph(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;...and {remaining} more.",
                        normal,
                    )
                )

    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("AI Recommendations", heading))
    story.append(Paragraph(str(ai_suggestions) or "No AI suggestions generated.", normal))

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "Upgrade to Premium for a full security audit (SSL/TLS, headers, "
            "cookies, CORS, sensitive paths and more) delivered as JSON and PDF.",
            normal,
        )
    )

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    return filename