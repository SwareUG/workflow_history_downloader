import os
import requests
import base64
import time
import logging
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

def get_repo_metadata(repo):
    owner, name = repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{name}"
    res = github_request_with_rate_handling(url)
    if res.status_code != 200:
        return None
    return res.json()

def get_workflow_files(repo):
    url = f"https://api.github.com/repos/{repo}/contents/.github/workflows"
    res = github_request_with_rate_handling(url)
    if res.status_code != 200:
        return []
    return [item['path'] for item in res.json() if item['name'].endswith('.yml')]

def get_commits_for_file(repo, path):
    url = f"https://api.github.com/repos/{repo}/commits"
    params = {"path": path, "per_page": 100}
    commits = []
    while url:
        res = github_request_with_rate_handling(url, params=params)
        if res.status_code != 200:
            break
        commits.extend(res.json())
        url = res.links.get("next", {}).get("url")
        params = None
    return commits

def get_file_content_at_commit(repo, path, sha):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    res = github_request_with_rate_handling(url, params={"ref": sha})
    if res.status_code != 200:
        return None
    content = res.json()
    if content.get("encoding") == "base64":
        return base64.b64decode(content["content"]).decode("utf-8")
    return None

def save_version_to_disk(repo_dir, filename, sha, content):
    name = filename.replace(".yml", f"_{sha}.yml")
    with open(os.path.join(repo_dir, name), "w", encoding="utf-8") as f:
        f.write(content)

def process_workflow_history(repo, wf_path, repo_dir):
    commits = get_commits_for_file(repo, wf_path)
    if not commits:
        return None
    first = commits[-1]["commit"]["committer"]["date"]
    last = commits[0]["commit"]["committer"]["date"]
    filename = os.path.basename(wf_path)
    for commit in commits:
        sha = commit["sha"]
        content = get_file_content_at_commit(repo, wf_path, sha)
        if content:
            save_version_to_disk(repo_dir, filename, sha, content)
    return {
        "version_count": len(commits),
        "first_commit_date": first,
        "last_commit_date": last
    }

def download_all_workflow_versions(repo, out_dir):
    metadata = get_repo_metadata(repo)
    if not metadata or metadata.get("archived", True):
        return {}, "skipped"

    os.makedirs(out_dir, exist_ok=True)
    owner, name = repo.split("/")
    repo_dir = os.path.join(out_dir, name)
    os.makedirs(repo_dir, exist_ok=True)

    workflows = get_workflow_files(repo)
    details = {}

    for wf_path in workflows:
        result = process_workflow_history(repo, wf_path, repo_dir)
        if result:
            details[os.path.basename(wf_path)] = result

    return details, f"✅ Downloaded {len(details)} workflow files for {repo}"
