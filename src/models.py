from dataclasses import dataclass
from enum import Enum

class Status(Enum):
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"
    ERROR = "error"

class Reason(Enum):
    OK = "ok"
    ALREADY_DOWNLOADED = "already_downloaded"
    NO_YML_WORKFLOWS = "no_yml_workflows"
    INVALID_REPO = "invalid_repo"
    EXCEPTION = "exception"

@dataclass
class RepoResult:
    repo_owner: str
    repo_name: str
    status: Status
    downloaded: int
    reason: Reason
    workflow_count: int = 0
    commit_count: int = 0
    error_message: str = ""

@dataclass
class ProcessingResult:
    summary: RepoResult
    workflows: dict
