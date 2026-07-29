import time
import requests


def test_website(url: str):
    start = time.time()

    try:
        response = requests.get(url, timeout=10)

        end = time.time()

        return {
            "status_code": response.status_code,
            "response_time": round(end - start, 2),
            "ssl_status": "Valid" if url.startswith("https") else "Invalid",
            "test_status": "Success"
        }

    except Exception:
        return {
            "status_code": 0,
            "response_time": 0,
            "ssl_status": "Unknown",
            "test_status": "Failed"
        }