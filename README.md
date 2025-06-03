
# workflow_history_downloader

Tool to download the history of GitHub Actions workflow files (`.yml`) from GitHub repositories.

## How to use

### Install dependencies

``pip install -r requirements.txt``

### Prepare input

Place your input file in the appropriate folder:

* `data/data_input/dependents/` → for JSON input (`MODE=json`)
* `data/data_input/repo_list/` → for CSV input (`MODE=csv`)


### Execute

From the `src` directory:

``MODE=csv python main.py``, or
``MODE=JSON python main.py``

### Output

Results are saved in:

* `data/data_output/workflows_from_dependents/` (if using JSON)
* `data/data_output/workflows_from_repo_list/` (if using CSV)
* `data/data_output/logs/workflow_versions.csv` (log of downloaded files)

