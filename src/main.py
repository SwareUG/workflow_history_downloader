import json
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import DISCLOSURE_DATA, log_path, json_dir, workflow_dir, log_dir
from utils import load_json, is_valid_repo
from processor import process_repository
from tqdm import tqdm

# === Asegurar que el directorio de logs existe
log_dir.mkdir(parents=True, exist_ok=True)

# === Configurar logging (archivo únicamente)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[logging.FileHandler(log_path)]
)

def process_action_dataset(action_key: str, config: dict) -> dict:
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

    # ✅ max_workers = 1 para controlar consumo de API
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {
            executor.submit(process_repository, repo, base_dir): repo
            for repo in filtered_repos
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc=f"{action_key}", ncols=80):
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


def build_workflow_summary() -> dict:
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_repositories": 0,
        "repositories": {}
    }

    for key, config in DISCLOSURE_DATA.items():
        repo_data = process_action_dataset(key, config)
        summary["repositories"].update(repo_data)
        summary["total_repositories"] += len(repo_data)

    return summary


def save_json_summary(data: dict):
    json_output_path = log_dir / "workflow_versions.json"
    with json_output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    summary_data = build_workflow_summary()
    save_json_summary(summary_data)


if __name__ == "__main__":
    main()
