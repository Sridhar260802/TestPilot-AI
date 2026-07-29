import time
import requests


def performance_check(url: str):
    start = time.time()

    response = requests.get(url, timeout=15)

    end = time.time()

    load_time = round(end - start, 2)

    score = 100

    if load_time > 1:
        score -= 10

    if load_time > 2:
        score -= 20

    if load_time > 3:
        score -= 30

    if score < 0:
        score = 0

    return {
        "status_code": response.status_code,
        "load_time": load_time,
        "performance_score": score
    }