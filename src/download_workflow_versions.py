import os
import base64
from pathlib import Path
from utils import github_request_with_rate_handling

def format_commit_date(date_str):
    return date_str.replace(":", "-")

def save_version_to_disk(repo_dir, filename, sha, commit_date, content, csv_records, repo_owner, repo_name):
    dt = format_commit_date(commit_date)
    base = filename.replace(".yml", "")
    new_name = f"{base}__{dt}__{sha}.yml"
    filepath = repo_dir / new_name
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    csv_records.append({
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "filename": new_name,
        "commit_date": commit_date
    })

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

def process_workflow_history(repo, wf_path, repo_dir, csv_records, repo_owner, repo_name):
    commits = get_commits_for_file(repo, wf_path)
    if not commits:
        return None
    first = commits[-1]["commit"]["committer"]["date"]
    last = commits[0]["commit"]["committer"]["date"]
    filename = os.path.basename(wf_path)
    for commit in commits:
        sha = commit["sha"]
        commit_date = commit["commit"]["committer"]["date"]
        content = get_file_content_at_commit(repo, wf_path, sha)
        if content:
            save_version_to_disk(repo_dir, filename, sha, commit_date, content, csv_records, repo_owner, repo_name)
    return {
        "version_count": len(commits),
        "first_commit_date": first,
        "last_commit_date": last
    }

def download_all_workflow_versions(repo, out_dir, csv_records, repo_owner, repo_name):
    metadata = get_repo_metadata(repo)
    if not metadata or metadata.get("archived", True):
        return {}, "skipped"

    os.makedirs(out_dir, exist_ok=True)
    repo_dir = out_dir / repo_name
    os.makedirs(repo_dir, exist_ok=True)

    workflows = get_workflow_files(repo)
    details = {}

    for wf_path in workflows:
        result = process_workflow_history(repo, wf_path, repo_dir, csv_records, repo_owner, repo_name)
        if result:
            details[os.path.basename(wf_path)] = result

    return details, f"✅ Downloaded {len(details)} workflow files for {repo}"
