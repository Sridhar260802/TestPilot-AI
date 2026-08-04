import subprocess
import tempfile
import os
import pathlib
import re


# =========================
# Python Analyzer
# =========================

def analyze_python_code(code: str):

    filename = None

    try:

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            delete=False,
            mode="w",
            encoding="utf-8",
            newline="\n"
        ) as f:

            f.write(code)
            filename = f.name


        result = subprocess.run(
            [
                "pylint",
                filename,
                "--output-format=text",
                "--disable=import-error"
            ],
            capture_output=True,
            text=True
        )
        print(result.stderr)
        print(result.stdout)
        print(result.returncode)


        report = result.stdout

        issues = re.findall(
            r".*?:\d+:\d+:\s+[CRWEF]\d+:\s+.*",
            report
        )

        score = 0

        match = re.search(
            r"rated at ([0-9.]+)/10",
            report
        )

        if match:
            score = round(
                float(match.group(1))*10
            )


        return {

            "tool": "Python Analyzer",

            "score": score,

            "issues": issues,

            "errors": result.stderr
        }


    finally:

        if filename and os.path.exists(filename):
            os.remove(filename)
    


# =========================
# JavaScript Analyzer
# =========================

def analyze_javascript_code(code: str):

    filename = None

    try:

        with tempfile.NamedTemporaryFile(
            suffix=".js",
            delete=False,
            mode="w",
            encoding="utf-8",
            newline="\n"
        ) as f:

            f.write(code)
            filename = f.name


        PROJECT_ROOT = pathlib.Path(
            __file__
        ).resolve().parents[2]


        result = subprocess.run(
            [
                r"C:\Users\user\AppData\Roaming\npm\eslint.cmd",
                filename
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )


        report = result.stdout


        issues = []


        for line in report.splitlines():

            if line.strip():
                issues.append(line.strip())


        error_count = report.lower().count("error")

        warning_count = report.lower().count("warning")


        score = 100

        score -= error_count * 10

        score -= warning_count * 5


        if score < 0:
            score = 0


        return {

            "tool": "JavaScript Analyzer",

            "score": score,

            "issues": issues,

            "errors": result.stderr
        }


    finally:

        if filename and os.path.exists(filename):
            os.remove(filename)