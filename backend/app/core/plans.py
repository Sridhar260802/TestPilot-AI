"""
Central definition of the three subscription tiers (Basic / Standard / Premium)
and a reusable FastAPI dependency that gates a route behind a minimum plan.

Adding a new tier or moving a feature between tiers only requires editing the
data in this file - no changes are needed in the routers that use `require_plan`.
"""

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_user
from app.models.user import User

# Higher number = more access. Every tier includes everything below it.
PLAN_RANK = {
    "basic": 1,
    "standard": 2,
    "premium": 3,
}

VALID_PLANS = tuple(PLAN_RANK.keys())

# Human readable feature matrix - used by GET /plans/features and to keep the
# routers self-documenting about what each tier actually contains.
PLAN_FEATURES = {
    "basic": {
        "name": "Basic Plan",
        "description": (
            "Essential evaluation features: basic SEO testing, basic accessibility "
            "testing, website availability checks, basic performance checks, basic "
            "content validation and basic image validation. Delivers a basic PDF "
            "report summarizing all checks."
        ),
        "includes": [
            "basic_seo",
            "basic_accessibility",
            "availability_check",
            "basic_performance",
            "basic_content_validation",
            "basic_image_validation",
            "basic_pdf_report",
        ],
    },
    "standard": {
        "name": "Standard Plan",
        "description": (
            "Everything in Basic, plus complete functional testing, navigation and "
            "link testing, forms and validation, authentication testing, responsive "
            "testing, browser compatibility, broken resource testing, advanced SEO, "
            "advanced accessibility, API validation, console error detection, AI "
            "recommendations and a detailed PDF report."
        ),
        "includes": [
            "functional_testing",
            "navigation_and_link_testing",
            "forms_and_validation",
            "authentication_testing",
            "responsive_testing",
            "browser_compatibility",
            "broken_resource_testing",
            "advanced_seo",
            "advanced_accessibility",
            "api_validation",
            "console_error_detection",
            "ai_recommendations",
            "detailed_pdf_report",
        ],
    },
    "premium": {
        "name": "Premium Plan",
        "description": (
            "Everything in Standard, plus a full security audit: SSL/TLS audit, "
            "SSL certificate validation, TLS cipher analysis, security headers "
            "audit, cookie security, CORS audit, HTTP/HTTPS audit, HTTP methods "
            "audit, sensitive path audit, mixed content audit, cache-control "
            "audit, information disclosure audit, security severity analysis and "
            "actionable security recommendations. Delivered as a security audit "
            "report in both JSON and PDF formats."
        ),
        "includes": [
            "ssl_tls_audit",
            "ssl_certificate_validation",
            "tls_cipher_analysis",
            "security_headers_audit",
            "cookie_security_audit",
            "cors_audit",
            "http_https_audit",
            "http_methods_audit",
            "sensitive_path_audit",
            "mixed_content_audit",
            "cache_control_audit",
            "information_disclosure_audit",
            "security_severity_analysis",
            "security_recommendations",
            "security_audit_json_and_pdf",
        ],
    },
}


def require_plan(min_plan: str):
    """
    Dependency factory. Use as:

        @router.post("/plans/premium/security-audit")
        def premium(..., current_user: User = Depends(require_plan("premium"))):
            ...

    Raises 403 if the authenticated user's plan does not meet `min_plan`.
    A user's `plan` covers every lower tier (premium unlocks standard + basic too).
    """

    if min_plan not in PLAN_RANK:
        raise ValueError(f"Unknown plan '{min_plan}'. Must be one of {VALID_PLANS}")

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        user_plan = (current_user.plan or "basic").lower()
        user_rank = PLAN_RANK.get(user_plan, PLAN_RANK["basic"])
        required_rank = PLAN_RANK[min_plan]

        if user_rank < required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This feature requires the '{min_plan}' plan or higher. "
                    f"Your current plan is '{user_plan}'. Upgrade via "
                    f"PUT /users/plan to access it."
                ),
            )

        return current_user

    return _dependency
