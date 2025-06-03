import logging
import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import DISCLOSURE_DATA, json_dir, workflow_dir, log_dir, log_path
from utils import load_json, is_valid_repo
from processor import process_repository

log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[logging.FileHandler(log_path)]
)

def save_json_summary(data: dict):
    json_output_path = log_dir / "workflow_versions.json"
    with json_output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def save_csv(csv_records):
    csv_path = log_dir / "workflow_versions.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["repo_owner", "repo_name", "filename", "commit_date"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_records:
            writer.writerow(row)

def process_action_dataset(action_key: str, config: dict, csv_records: list) -> dict:
    json_path = json_dir / config["json_filename"]
    data = load_json(json_path)
    if data is None:
        logging.warning(f"No se pudo cargar el archivo JSON: {json_path}")
        return {}

    dependents = data.get("dependents", [])
    base_dir = workflow_dir / action_key
    base_dir.mkdir(parents=True, exist_ok=True)

    filtered_repos = [
        entry["full_name"]
        for entry in dependents
        if entry.get("full_name") and is_valid_repo(entry)
    ]

    logging.info(f"{action_key} — total dependents: {len(dependents)}, válidos: {len(filtered_repos)}")

    repo_data = {}

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {
            executor.submit(process_repository, repo, base_dir, csv_records): repo
            for repo in filtered_repos
        }

        for future in as_completed(futures):
            processing = future.result()
            result = processing.summary
            details = processing.workflows

            logging.info(f"{result.repo_owner}/{result.repo_name} — {result.status.value} — {result.reason.value}")

            repo_key = f"{result.repo_owner}/{result.repo_name}"
            repo_data[repo_key] = {
                "status": result.status.value,
                "downloaded": result.downloaded,
                "reason": result.reason.value,
                "workflow_count": len(details),
                "workflows": details
            }

    return repo_data

def build_workflow_summary(csv_records) -> dict:
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_repositories": 0,
        "repositories": {}
    }

    for key, config in DISCLOSURE_DATA.items():
        repo_data = process_action_dataset(key, config, csv_records)
        summary["repositories"].update(repo_data)
        summary["total_repositories"] += len(repo_data)

    return summary

def main():
    csv_records = []
    summary_data = build_workflow_summary(csv_records)
    save_json_summary(summary_data)
    save_csv(csv_records)

if __name__ == "__main__":
    main()
