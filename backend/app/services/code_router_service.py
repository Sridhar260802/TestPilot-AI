from app.services.code_analysis_service import analyze_python_code
from app.services.code_analysis_service import analyze_javascript_code
from app.services.html_analysis_service import analyze_html_code
from app.services.css_analysis_service import analyze_css_code
from app.services.react_analysis_service import analyze_react_code
from app.services.java_analysis_service import analyze_java_code


def analyze_code_by_extension(
    extension,
    code
):

    if extension == ".py":
        return analyze_python_code(code)


    elif extension == ".js":
        return analyze_javascript_code(code)


    elif extension == ".jsx":
        return analyze_react_code(code)


    elif extension == ".html":
        return analyze_html_code(code)


    elif extension == ".css":
        return analyze_css_code(code)


    elif extension == ".java":
        return analyze_java_code(code)


    else:
        return {
            "error": "Unsupported language"
        }