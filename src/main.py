import logging
import json
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from config import (
    MODE, INPUT_FILENAME, json_dir, csv_dir,
    workflow_dir, log_dir, log_path
)
from utils import load_json, load_repo_list_from_csv, is_valid_repo
from processor import process_repository

# === Asegurar que el directorio de logs existe
log_dir.mkdir(parents=True, exist_ok=True)

# === Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[logging.FileHandler(log_path)]
)

def save_csv(csv_records):
    csv_path = log_dir / "workflow_versions.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["repo_owner", "repo_name", "filename", "commit_date"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_records:
            writer.writerow(row)

def get_filtered_repos():
    if MODE == "json":
        json_path = json_dir / INPUT_FILENAME
        data = load_json(json_path)
        if data is None:
            raise RuntimeError(f"No se pudo cargar el archivo JSON: {json_path}")
        dependents = data.get("dependents", [])
        return [d["full_name"] for d in dependents if d.get("full_name") and is_valid_repo(d)]

    elif MODE == "csv":
        csv_path = csv_dir / INPUT_FILENAME
        return load_repo_list_from_csv(csv_path)

    else:
        raise ValueError("MODE debe ser 'json' o 'csv'")

def main():
    csv_records = []
    filtered_repos = get_filtered_repos()
    logging.info(f"Repositorios válidos: {len(filtered_repos)}")

    if MODE == "json":
        base_dir = workflow_dir / "workflows_from_dependents"
    elif MODE == "csv":
        base_dir = workflow_dir / "workflows_from_repo_list"
    else:
        raise ValueError("MODE debe ser 'json' o 'csv'")

    base_dir.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {
            executor.submit(process_repository, repo, base_dir, csv_records): repo
            for repo in filtered_repos
        }

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Processing Repositories",
            ncols=80,
            dynamic_ncols=True,
            leave=True,
            file=sys.stdout
        ):
            result = future.result().summary
            logging.info(f"{result.repo_owner}/{result.repo_name} — {result.status.value} — {result.reason.value}")

    save_csv(csv_records)

if __name__ == "__main__":
    main()
