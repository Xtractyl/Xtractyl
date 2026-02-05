# orchestrator/domain/projects.py

import json
import os

import requests
from flask import jsonify, request

# Fixed base dir (no env lookups)
BASE_PROJECTS_DIR = os.path.join("data", "projects")

# === Base URLs / Ports (from env with defaults) ===
LABELSTUDIO_HOST = os.getenv("LABELSTUDIO_CONTAINER_NAME", "labelstudio")
LABELSTUDIO_PORT = os.getenv("LABELSTUDIO_PORT", "8080")
LABEL_STUDIO_URL = f"http://{LABELSTUDIO_HOST}:{LABELSTUDIO_PORT}"

ML_BACKEND_HOST = os.getenv("ML_BACKEND_CONTAINER_NAME", "ml_backend")
ML_BACKEND_PORT = os.getenv("ML_BACKEND_PORT", "6789")
ML_BACKEND_URL = f"http://{ML_BACKEND_HOST}:{ML_BACKEND_PORT}"

BATCH_SIZE = 50


def check_project_exists():
    try:
        data = request.get_json()
        title = data.get("title")
        if not title:
            return jsonify({"error": "Missing 'title' in request body"}), 400

        project_path = os.path.join("data", "projects", title)
        exists = os.path.exists(project_path)

        return jsonify({"exists": exists}), 200

    except Exception:
        return jsonify({"error": "internal error"}), 500


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

    # Inputs from payload
    title = payload.get("title", "xtractyl_project")
    questions = payload.get("questions", [])
    labels = payload.get("labels", [])
    token = payload.get("token")

    if not all([title, questions, labels, token]):
        raise ValueError("Missing required fields: title, questions, labels, token.")

    # Create project folder
    base_path = os.path.join("data", "projects", title)
    os.makedirs(base_path, exist_ok=True)

    # Save questions_and_labels.json
    qa_path = os.path.join(base_path, "questions_and_labels.json")
    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump({"questions": questions, "labels": labels}, f, indent=2, ensure_ascii=False)

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
            f"{LABEL_STUDIO_URL}/api/projects",
            headers=headers,
            json=project_payload,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException:
        raise RuntimeError("Label Studio project creation failed")

    project_id = response.json().get("id")
    if not project_id:
        raise RuntimeError("Label Studio project creation failed (no id)")

    # Attach ML backend
    ml_payload = {"url": ML_BACKEND_URL, "title": "xtractyl-backend", "project": project_id}
    try:
        ml_response = requests.post(
            f"{LABEL_STUDIO_URL}/api/ml",
            headers=headers,
            json=ml_payload,
            timeout=20,
        )
        ml_response.raise_for_status()
    except requests.RequestException:
        raise RuntimeError("Couldn't attach ML Backend")

    return {"project_id": project_id}


def list_html_subfolders():
    base_dir = os.path.join("data", "htmls")
    try:
        subfolders = [
            name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))
        ]
        return jsonify(subfolders), 200
    except Exception:
        return jsonify({"error": "internal error"}), 500


def _safe_join(base: str, *paths: str) -> str:
    """Prevent path traversal by resolving and checking commonprefix."""
    full = os.path.abspath(os.path.join(base, *paths))
    base_abs = os.path.abspath(base)
    if not os.path.commonprefix([full, base_abs]) == base_abs:
        raise ValueError("Invalid path")
    return full


def list_projects_route():
    """
    GET /list_projects
    Returns: ["ProjectA", "ProjectB", ...]
    Lists folders directly under data/projects.
    """
    try:
        if not os.path.isdir(BASE_PROJECTS_DIR):
            return jsonify([]), 200
        items = sorted(
            d
            for d in os.listdir(BASE_PROJECTS_DIR)
            if os.path.isdir(os.path.join(BASE_PROJECTS_DIR, d))
        )
        return jsonify(items), 200
    except Exception:
        return jsonify({"error": "internal error"}), 500


def list_qal_jsons_route():
    """
    GET /list_qal_jsons?project=<name>
    Returns: ["questions_and_labels.json", ...]
    Lists *.json files in the project's folder.
    """
    project = (request.args.get("project") or "").strip()
    if not project:
        return jsonify({"error": "missing 'project'"}), 400

    try:
        project_dir = _safe_join(BASE_PROJECTS_DIR, project)
        if not os.path.isdir(project_dir):
            return jsonify([]), 200

        files = sorted(
            f
            for f in os.listdir(project_dir)
            if f.lower().endswith(".json") and os.path.isfile(os.path.join(project_dir, f))
        )
        return jsonify(files), 200
    except ValueError:
        return jsonify({"error": "invalid path"}), 400
    except Exception:
        return jsonify({"error": "internal error"}), 500


def preview_qal_route():
    """
    GET /preview_qal?project=<name>&file=<filename.json>
    Returns: parsed JSON of the file (object or array).
    """
    project = (request.args.get("project") or "").strip()
    filename = (request.args.get("file") or "").strip()
    if not project or not filename:
        return jsonify({"error": "missing 'project' or 'file'"}), 400
    if not filename.lower().endswith(".json"):
        return jsonify({"error": "file must be a .json"}), 400

    try:
        project_dir = _safe_join(BASE_PROJECTS_DIR, project)
        file_path = _safe_join(project_dir, filename)
        if not os.path.isfile(file_path):
            return jsonify({"error": "file not found"}), 404

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    except ValueError:
        return jsonify({"error": "invalid path"}), 400
    except json.JSONDecodeError:
        return jsonify({"error": "invalid JSON"}), 400
    except Exception:
        return jsonify({"error": "internal error"}), 500


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


def upload_in_batches(tasks, batch_size, project_id, headers):
    """Upload tasks to Label Studio in batches."""
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks/bulk"
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i : i + batch_size]
        resp = requests.post(url, headers=headers, json=batch, timeout=30)
        if resp.status_code != 201:
            raise RuntimeError(f"Upload failed: {resp.status_code}")


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
        raise FileNotFoundError("Folder not found.")

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    # Fetch projects
    r = requests.get(f"{LABEL_STUDIO_URL}/api/projects", headers=headers, timeout=30)
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
        raise ValueError("Project not found in Label Studio.")

    tasks = collect_html_tasks(html_folder)

    if tasks:
        upload_in_batches(tasks, BATCH_SIZE, project_id, headers)

    return {"status": "ok"}
