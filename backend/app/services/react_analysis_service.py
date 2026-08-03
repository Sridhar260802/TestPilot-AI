import re


def analyze_react_code(code: str):

    issues = []


    if "export default" not in code:
        issues.append(
            "Missing export default"
        )


    if "return (" not in code:
        issues.append(
            "Missing return statement"
        )


    if "class=" in code:
        issues.append(
            "Use className instead of class"
        )


    if ".map(" in code and "key=" not in code:
        issues.append(
            "Missing key prop in list rendering"
        )


    if "useEffect(" in code and "[]" not in code:
        issues.append(
            "Possible missing dependency array in useEffect"
        )


    if "console.log(" in code:
        issues.append(
            "Remove console.log before production"
        )


    if "any" in code:
        issues.append(
            "Avoid using any type"
        )


    score = 100 - (len(issues) * 10)

    if score < 0:
        score = 0


    return {

        "tool": "React Analyzer",

        "score": score,

        "issues": issues,

        "errors": ""

    }