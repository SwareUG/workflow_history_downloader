import json

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
