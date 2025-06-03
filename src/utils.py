import os
import time
import json
import csv
import requests
from dotenv import load_dotenv

# === Cargar token de entorno
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# === Cabeceras de autenticación para GitHub API
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

def load_repo_list_from_csv(path):
    repos = []
    try:
        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                owner = row.get("repo_owner", "").strip()
                name = row.get("repo_name", "").strip()
                if owner and name:
                    repos.append(f"{owner}/{name}")
    except Exception as e:
        print(f"Error al leer CSV: {e}")
    return repos

def is_valid_repo(repo_dict: dict) -> bool:
    return (
        not repo_dict.get("archived", True) and
        repo_dict.get("stars", 0) <= 10 and
        repo_dict.get("size", 0) >= 10
    )
