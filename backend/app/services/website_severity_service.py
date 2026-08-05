def calculate_website_severity(health_score: int):

    if health_score >= 90:
        return "Low"

    elif health_score >= 75:
        return "Medium"

    elif health_score >= 60:
        return "High"

    else:
        return "Critical"