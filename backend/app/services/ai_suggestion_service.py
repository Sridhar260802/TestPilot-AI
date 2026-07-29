def generate_ai_suggestions(
    health_score: int,
    broken_links: int,
    seo_score: int,
    accessibility_score: int,
    performance_score: int
):
    suggestions = []

    if broken_links > 0:
        suggestions.append(f"Fix {broken_links} broken links.")

    if seo_score < 90:
        suggestions.append("Improve SEO by adding meta tags and headings.")

    if accessibility_score < 90:
        suggestions.append("Improve accessibility by adding ALT text and button labels.")

    if performance_score < 90:
        suggestions.append("Optimize website performance by compressing images and reducing load time.")

    if health_score < 80:
        suggestions.append("Overall website health is low. Review all critical issues.")

    if not suggestions:
        suggestions.append("Excellent! Your website follows most best practices.")

    return {
        "health_score": health_score,
        "ai_suggestions": suggestions
    }