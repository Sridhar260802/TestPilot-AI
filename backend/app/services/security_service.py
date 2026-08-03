import requests


def security_check(url: str):

    try:

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        headers = response.headers

        https = url.startswith("https")

        hsts = (
            "Strict-Transport-Security"
            in headers
        )

        csp = (
            "Content-Security-Policy"
            in headers
        )

        x_frame = (
            "X-Frame-Options"
            in headers
        )

        x_content = (
            "X-Content-Type-Options"
            in headers
        )

        referrer = (
            "Referrer-Policy"
            in headers
        )

        permissions = (
            "Permissions-Policy"
            in headers
        )

        coop = (
            "Cross-Origin-Opener-Policy"
            in headers
        )

        corp = (
            "Cross-Origin-Resource-Policy"
            in headers
        )

        score = 0

        if https:
            score += 20

        if hsts:
            score += 10

        if csp:
            score += 15

        if x_frame:
            score += 10

        if x_content:
            score += 10

        if referrer:
            score += 10

        if permissions:
            score += 10

        if coop:
            score += 10

        if corp:
            score += 5

        if score >= 90:
            grade = "A"

        elif score >= 75:
            grade = "B"

        elif score >= 60:
            grade = "C"

        else:
            grade = "D"

        return {

            "security_score": score,

            "grade": grade,

            "https": https,

            "hsts": hsts,

            "content_security_policy": csp,

            "x_frame_options": x_frame,

            "x_content_type_options": x_content,

            "referrer_policy": referrer,

            "permissions_policy": permissions,

            "cross_origin_opener_policy": coop,

            "cross_origin_resource_policy": corp

        }

    except Exception as e:

        return {

            "error": str(e)

        }