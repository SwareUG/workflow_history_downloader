from pathlib import Path

# === Ruta base del proyecto
root_dir = Path(__file__).resolve().parent.parent

# === Rutas de entrada y salida
json_dir = root_dir / "data_input"
workflow_dir = root_dir / "data_output" / "workflows_raw"
log_dir = root_dir / "data_output" / "logs"
log_path = log_dir / "execution.log"

# === Acciones vulnerables a procesar
DISCLOSURE_DATA = {
    "tj-actions__branch-names": {
        "json_filename": "tj-actions__branch-names.json",
        "actions_to_track": {
            "tj-actions/branch-names": {
                "disclosure_date": "2023-12-04",
                "affected_version": "7.0.6"
            }
        }
    }
}
