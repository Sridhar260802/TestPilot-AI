import re


def analyze_java_code(code: str):

    issues = []


    if "class " not in code:
        issues.append(
            "Missing class declaration"
        )


    if "public static void main" not in code:
        issues.append(
            "Missing main method"
        )


    if "System.out.println" not in code:
        issues.append(
            "No output statement found"
        )


    if "import java." not in code:
        issues.append(
            "No import statements found"
        )


    if "try" not in code and "catch" not in code:
        issues.append(
            "Exception handling not found"
        )


    if "finally" not in code:
        issues.append(
            "No finally block used"
        )


    if "new Scanner" in code and ".close()" not in code:
        issues.append(
            "Scanner object not closed"
        )


    if "==" in code and ".equals(" not in code:
        issues.append(
            "Use .equals() for String comparison"
        )


    if "public class" not in code:
        issues.append(
            "Class should be declared as public"
        )


    score = 100 - (len(issues) * 10)

    if score < 0:
        score = 0


    return {

        "tool": "Java Analyzer",

        "score": score,

        "issues": issues,

        "errors": ""

    }