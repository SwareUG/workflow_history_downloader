from pathlib import Path
import os

# === Ruta base del proyecto
root_dir = Path(__file__).resolve().parent.parent

# === Raíz unificada bajo 'data'
data_input_root = root_dir / "data" / "data_input"
data_output_root = root_dir / "data" / "data_output"

# === Rutas de entrada
json_dir = data_input_root / "dependents"
csv_dir = data_input_root / "repo_list"

# === Modo de operación
MODE = os.getenv("MODE", "json").lower()

# === Detectar automáticamente el archivo de entrada
def find_first_file(directory: Path, extension: str):
    files = sorted(directory.glob(f"*.{extension}"))
    if not files:
        raise FileNotFoundError(f"No se encontró ningún archivo .{extension} en {directory}")
    return files[0].name

if MODE == "json":
    INPUT_FILENAME = find_first_file(json_dir, "json")
    workflow_dir = data_output_root / "workflows_from_dependents"
    log_dir = data_output_root / "logs" / "logs_from_dependents"
elif MODE == "csv":
    INPUT_FILENAME = find_first_file(csv_dir, "csv")
    workflow_dir = data_output_root / "workflows_from_repo_list"
    log_dir = data_output_root / "logs" / "logs_from_repo_list"
else:
    raise ValueError("MODE debe ser 'json' o 'csv'")

log_path = log_dir / "execution.log"
