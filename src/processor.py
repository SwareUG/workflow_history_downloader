import logging
from pathlib import Path
from models import RepoResult, Status, Reason, ProcessingResult
from download_workflow_versions import download_all_workflow_versions, get_workflow_files

def process_repository(repo: str, base_dir: Path) -> ProcessingResult:
    try:
        owner, name = repo.split("/")
    except ValueError:
        return ProcessingResult(
            summary=RepoResult(repo, "", Status.ERROR, 0, Reason.INVALID_REPO, 0, 0, "invalid repo format"),
            workflows={}
        )

    repo_dir = base_dir / owner / name
    if repo_dir.exists():
        return ProcessingResult(
            summary=RepoResult(owner, name, Status.SKIPPED, 0, Reason.ALREADY_DOWNLOADED),
            workflows={}
        )

    workflow_files = get_workflow_files(repo)
    if not workflow_files:
        return ProcessingResult(
            summary=RepoResult(owner, name, Status.SKIPPED, 0, Reason.NO_YML_WORKFLOWS),
            workflows={}
        )

    try:
        details, message = download_all_workflow_versions(repo=repo, out_dir=base_dir / owner)
        downloaded_flag = 1 if "Downloaded" in message else 0
        workflow_count = len(details)
        commit_count = sum(d["version_count"] for d in details.values())

        return ProcessingResult(
            summary=RepoResult(owner, name, Status.DOWNLOADED, downloaded_flag, Reason.OK, workflow_count, commit_count),
            workflows=details
        )
    except Exception as e:
        logging.error(f"{repo} — exception: {e}")
        return ProcessingResult(
            summary=RepoResult(owner, name, Status.ERROR, 0, Reason.EXCEPTION, 0, 0, str(e)),
            workflows={}
        )