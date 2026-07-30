import subprocess
import tempfile
import os
import pathlib

def analyze_python_code(code: str):
    with tempfile.NamedTemporaryFile(
        suffix=".py",
        delete=False,
        mode="w",
        encoding="utf-8"
    ) as f:
        f.write(code)
        filename = f.name

    try:
        result = subprocess.run(
            ["pylint", filename, "--output-format=text"],
            capture_output=True,
            text=True
        )

        return {
            "tool": "Pylint",
            "report": result.stdout,
            "errors": result.stderr
        }

    finally:
        os.remove(filename)
        
def analyze_javascript_code(code: str):
    with tempfile.NamedTemporaryFile(
        suffix=".js",
        delete=False,
        mode="w",
        encoding="utf-8"
    ) as f:
        f.write(code)
        filename = f.name

    try:
        PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [
                r"C:\Users\user\AppData\Roaming\npm\eslint.cmd",
                filename
            ],
            cwd=str(PROJECT_ROOT),
            
            capture_output=True,
            text=True
        )

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        return {
            "tool": "ESLint",
            "report": result.stdout,
            "errors": result.stderr
        }

    finally:
        os.remove(filename)      