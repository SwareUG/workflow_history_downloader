import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def github_request_with_rate_handling(url, params=None):
    while True:
        res = requests.get(url, headers=HEADERS, params=params)
        if res.status_code == 403:
            remaining = int(res.headers.get("X-RateLimit-Remaining", "1"))
            reset_ts = int(res.headers.get("X-RateLimit-Reset", "0"))
            now_ts = int(time.time())
            if remaining == 0 and reset_ts > now_ts:
                time.sleep(reset_ts - now_ts + 5)
                continue
        return res

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def is_valid_repo(repo_dict: dict) -> bool:
    return (
        not repo_dict.get("archived", True) and
        repo_dict.get("stars", 0) <= 10 and
        repo_dict.get("size", 0) >= 10
    )
