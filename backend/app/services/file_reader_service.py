import os


def read_code_file(file):

    filename = file.filename

    extension = os.path.splitext(filename)[1].lower()

    supported = [
        ".py",
        ".js",
        ".jsx",
        ".html",
        ".css",
        ".java"
    ]

    if extension not in supported:
        return {
            "error": "Unsupported file type"
        }


    content = file.file.read()

    code = content.decode(
        "utf-8",
        errors="ignore"
    ).replace("\r\n", "\n").replace("\r", "\n")


    return {
        "filename": filename,
        "extension": extension,
        "code": code
    }