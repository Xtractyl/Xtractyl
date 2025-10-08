import logging
import os

import requests

# === Base URLs / Ports (from env with defaults) ===
LABELSTUDIO_HOST = os.getenv("LABELSTUDIO_CONTAINER_NAME", "labelstudio")
LABELSTUDIO_PORT = os.getenv("LABELSTUDIO_PORT", "8080")
LABEL_STUDIO_URL = f"http://{LABELSTUDIO_HOST}:{LABELSTUDIO_PORT}"

BATCH_SIZE = 50

# === Logging ===
LOGFILE_PATH = "/logs/orchestrator.log"
os.makedirs(os.path.dirname(LOGFILE_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOGFILE_PATH, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def collect_html_tasks(folder: str):
    """Collect HTML files from a folder and build Label Studio task payloads."""
    tasks = []
    for filename in os.listdir(folder):
        if filename.endswith(".html"):
            path = os.path.join(folder, filename)
            with open(path, encoding="utf-8") as f:
                html = f.read()
                # include filename as a task attribute
                tasks.append(
                    {
                        "data": {
                            "html": html,
                            "name": filename,
                        }
                    }
                )
    return tasks


def upload_in_batches(tasks, batch_size, logs, project_id, headers):
    """Upload tasks to Label Studio in batches, append progress to logs and logger."""
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks/bulk"
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i : i + batch_size]
        try:
            resp = requests.post(url, headers=headers, json=batch)
            msg = f"📦 Batch {i // batch_size + 1}: {resp.status_code}"
            logs.append(msg)
            logger.info(msg)

            if resp.status_code != 201:
                logs.append("❌ Upload failed.")
                logs.append(resp.text)
                logger.error("Upload failed.")
                logger.error(resp.text)
                break
        except Exception as e:
            err = f"❌ Upload error: {e}"
            logs.append(err)
            logger.exception(err)
            break


def upload_tasks_main_from_payload(payload: dict):
    """
    Upload HTML files from the selected folder as tasks to an existing Label Studio project.

    Expected payload:
      - project_name: str
      - token: str  (Label Studio legacy token)
      - html_folder: str (subfolder inside data/htmls)
    """
    title = payload.get("project_name")
    token = payload.get("token")
    html_folder_name = payload.get("html_folder")

    if not title or not token or not html_folder_name:
        raise ValueError("project_name, token, and html_folder are required.")

    html_folder = os.path.join("data", "htmls", html_folder_name)
    if not os.path.isdir(html_folder):
        raise FileNotFoundError(f"Folder not found: {html_folder}")

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    # Fetch projects
    r = requests.get(f"{LABEL_STUDIO_URL}/api/projects", headers=headers)
    if r.status_code != 200:
        raise RuntimeError("Could not load projects from Label Studio.")

    projects_json = r.json()
    projects = (
        projects_json
        if isinstance(projects_json, list)
        else projects_json.get("projects") or projects_json.get("results") or []
    )
    project_id = next((p["id"] for p in projects if p.get("title") == title), None)

    if not project_id:
        raise ValueError(f"Project '{title}' not found in Label Studio.")

    logs = [f"🔍 Scanning HTML files in {html_folder} ..."]
    logger.info(logs[-1])

    tasks = collect_html_tasks(html_folder)
    msg = f"📄 Found {len(tasks)} HTML file(s)."
    logs.append(msg)
    logger.info(msg)

    if tasks:
        upload_in_batches(tasks, BATCH_SIZE, logs, project_id, headers)
    else:
        msg = "⚠️ No HTML files found."
        logs.append(msg)
        logger.warning(msg)

    # Persist a simple run summary to the orchestrator log (already handled via logger)
    summary = "Upload completed." if tasks else "Nothing to upload."
    logger.info(summary)
    logs.append(summary)

    return logs
