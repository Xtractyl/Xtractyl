# orchestrator/routes/create_project.py
import json
import os
from datetime import datetime

import requests

# === Base URLs / Ports (resolve from env or defaults) ===
LABEL_STUDIO_URL = f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:{os.getenv('LABELSTUDIO_PORT', '8080')}"
ML_BACKEND_URL = f"http://{os.getenv('ML_BACKEND_CONTAINER_NAME', 'ml_backend')}:{os.getenv('ML_BACKEND_PORT', '6789')}"

LOGFILE_PATH = "/logs/orchestrator.log"


def log_to_file(message: str) -> None:
    """Append a timestamped log line to the orchestrator log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGFILE_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def create_project_main_from_payload(payload: dict):
    """
    Create a Label Studio project and store the provided questions/labels alongside it.
    Also attempts to attach the ML backend to the created project.

    Expected payload keys:
      - title: str
      - questions: list[str]
      - labels: list[str]
      - token: str (Label Studio legacy token)
    """
    logs = []

    # Inputs from payload
    title = payload.get("title", "xtractyl_project")
    questions = payload.get("questions", [])
    labels = payload.get("labels", [])
    token = payload.get("token")

    log_to_file(f"Project creation started for: '{title}'")
    log_to_file(f"Questions: {questions}")
    log_to_file(f"Labels: {labels}")

    if not all([title, questions, labels, token]):
        msg = "Missing required fields: title, questions, labels, token."
        log_to_file(f"ERROR: {msg}")
        raise ValueError(msg)

    # Create project folder
    base_path = os.path.join("data", "projects", title)
    os.makedirs(base_path, exist_ok=True)
    log_to_file(f"Ensured project directory exists: {base_path}")

    # Save questions_and_labels.json
    qa_path = os.path.join(base_path, "questions_and_labels.json")
    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump({"questions": questions, "labels": labels}, f, indent=2, ensure_ascii=False)
    msg = f"Saved questions_and_labels.json at: {qa_path}"
    logs.append(msg)
    log_to_file(msg)

    # Label Studio label config
    label_tags = "\n    ".join([f'<Label value="{label}"/>' for label in labels])
    label_config = f"""
    <View>
        <View style="padding: 0.5em 1em; background: #f7f7f7; border-radius: 4px; margin-bottom: 0.5em;">
            <Header value="File: $name" style="font-weight:bold; font-size: 16px; color: #333;" />
        </View>
        <View style="padding: 0 1em; margin: 1em 0; background: #f1f1f1; position: sticky; top: 0; border-radius: 3px; z-index:100">
            <Labels name="label" toName="html">
                {label_tags}
            </Labels>
        </View>
        <HyperText name="html" value="$html" granularity="symbol" />
    </View>"""

    # Create project via API
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    project_payload = {"title": title, "label_config": label_config}

    try:
        response = requests.post(
            f"{LABEL_STUDIO_URL}/api/projects", headers=headers, json=project_payload
        )
    except Exception as e:
        log_to_file(f"ERROR: Network error while creating project: {e}")
        raise

    if response.status_code != 201:
        error_msg = f"Failed to create project: {response.text}"
        logs.append(error_msg)
        log_to_file(f"ERROR: {error_msg}")
        raise RuntimeError(error_msg)

    project_id = response.json()["id"]
    msg = f"Project '{title}' created with ID {project_id}"
    logs.append(msg)
    log_to_file(msg)

    # Attach ML backend
    ml_payload = {"url": ML_BACKEND_URL, "title": "xtractyl-backend", "project": project_id}
    try:
        ml_response = requests.post(f"{LABEL_STUDIO_URL}/api/ml", headers=headers, json=ml_payload)
    except Exception as e:
        log_to_file(f"WARNING: Network error while attaching ML backend: {e}")
        raise

    if ml_response.status_code != 201:
        msg = f"WARNING: Could not attach ML backend: {ml_response.text}"
        logs.append(msg)
        log_to_file(msg)
    else:
        msg = "ML backend successfully attached."
        logs.append(msg)
        log_to_file(msg)

    return logs
