# orchestrator/domain/projects.py
import json
import os

import requests
from flask import jsonify, request

from domain.errors import (
    DomainError,
    ExternalServiceError,
    InternalError,
    NotFound,
    ValidationFailed,
)
from domain.models.projects import CreateProjectCommand, ListQalJsonsCommand, PreviewQalCommand

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
        gt_path = os.path.join("data", "projects", "Evaluation_Sets_Do_Not_Delete", title)
        exists = os.path.exists(project_path) or os.path.exists(gt_path)

        return jsonify({"exists": exists}), 200

    except Exception:
        return jsonify({"error": "internal error"}), 500


def create_project_main_from_payload(cmd: CreateProjectCommand):
    """
    Create a Label Studio project and store the provided questions/labels alongside it.
    Also attempts to attach the ML backend to the created project.

    Args:
        cmd: CreateProjectCommand with title, token, questions, and labels.

    Returns:
        {"project_id": int} on success.

    Raises:
        ExternalServiceError: If Label Studio is unreachable or returns no project id.
        ExternalServiceError: If ML backend cannot be attached to the project.
    """
    title = cmd.title
    questions = cmd.questions
    labels = cmd.labels
    token = cmd.token

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
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Label Studio project creation failed.",
        )

    project_id = response.json().get("id")
    if not project_id:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Label Studio project creation failed.",
        )

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
        raise ExternalServiceError(
            code="ML_BACKEND_UNAVAILABLE",
            message="Could not attach ML backend to project.",
        )

    return {"project_id": project_id}


def list_html_subfolders():
    """
    List all subfolders in the HTML base directory.
    Includes subfolders of Evaluation_Sets_Do_Not_Delete as relative paths.

    Returns:
        {"subfolders": list[str]} — alphabetically sorted folder names.

    Raises:
        InternalError: If the directory cannot be read.
    """
    base_dir = os.path.join("data", "htmls")
    gt_sets_dir = os.path.join("data", "htmls", "Evaluation_Sets_Do_Not_Delete")
    try:
        subfolders = sorted(
            name
            for name in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, name))
            and name != "Evaluation_Sets_Do_Not_Delete"
        )
        if os.path.isdir(gt_sets_dir):
            gt_subfolders = sorted(
                os.path.join("Evaluation_Sets_Do_Not_Delete", name)
                for name in os.listdir(gt_sets_dir)
                if os.path.isdir(os.path.join(gt_sets_dir, name))
            )
            subfolders = gt_subfolders + subfolders
        return {"subfolders": subfolders}
    except Exception:
        raise InternalError(
            code="INTERNAL_ERROR",
            message="Could not list HTML subfolders.",
        )


def _safe_join(base: str, *paths: str) -> str:
    """Prevent path traversal by resolving and checking commonprefix."""
    full = os.path.abspath(os.path.join(base, *paths))
    base_abs = os.path.abspath(base)
    if not os.path.commonprefix([full, base_abs]) == base_abs:
        raise ValueError("Invalid path")
    return full


def list_qal_jsons(cmd: ListQalJsonsCommand):
    """
    List all .json files in a project's folder.

    Args:
        cmd: ListQalJsonsCommand with project name.

    Returns:
        {"files": list[str]} — empty list if project folder does not exist.

    Raises:
        ValidationFailed: If the project path is invalid (path traversal attempt).
        InternalError: If the folder cannot be read.
    """
    project = cmd.project
    try:
        project_dir = _safe_join(BASE_PROJECTS_DIR, project)
        if not os.path.isdir(project_dir):
            return {"files": []}

        files = sorted(
            f
            for f in os.listdir(project_dir)
            if f.lower().endswith(".json") and os.path.isfile(os.path.join(project_dir, f))
        )
        return {"files": files}
    except ValueError:
        raise ValidationFailed(
            code="INVALID_PATH",
            message="Invalid project path.",
        )
    except Exception:
        raise InternalError(
            code="INTERNAL_ERROR",
            message="Could not list QAL json files.",
        )


def preview_qal(cmd: PreviewQalCommand):
    """
    Read and return the content of a QAL JSON file for a given project.

    Args:
        cmd: PreviewQalCommand with project name and filename.

    Returns:
        {"data": dict} — parsed JSON content of the file.

    Raises:
        ValidationFailed: If the project or file path is invalid (path traversal attempt).
        NotFound: If the file does not exist.
        InternalError: If the file contains invalid JSON or cannot be read.
    """
    try:
        project = cmd.project
        filename = cmd.filename
        project_dir = _safe_join(BASE_PROJECTS_DIR, project)
        file_path = _safe_join(project_dir, filename)
        if not os.path.isfile(file_path):
            raise NotFound(
                code="QAL_FILE_NOT_FOUND",
                message="QAL file not found.",
            )
        with open(file_path, encoding="utf-8") as f:
            content = json.load(f)
        return {"data": content}
    except ValueError:
        raise ValidationFailed(
            code="INVALID_PATH",
            message="Invalid project or file path.",
        )
    except json.JSONDecodeError:
        raise InternalError(
            code="INVALID_JSON",
            message="QAL file contains invalid JSON.",
        )
    except DomainError:
        raise
    except Exception:
        raise InternalError(
            code="INTERNAL_ERROR",
            message="Could not read QAL file.",
        )


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
            raise ExternalServiceError(
                code="LABEL_STUDIO_UNAVAILABLE",
                message=f"Task upload failed with status {resp.status_code}.",
            )


def upload_tasks_main_from_payload(payload: dict, token: str):
    """
    Upload HTML files from the selected folder as tasks to an existing Label Studio project.

    Args:
        payload: Dict with project_name and html_folder.
        token: Label Studio API token.

    Returns:
        {"status": "ok"} on success.

    Raises:
        ValidationFailed: If required fields are missing.
        NotFound: If the folder or project does not exist in Label Studio.
        ExternalServiceError: If Label Studio is unreachable or upload fails.
    """
    title = payload.get("project_name")
    html_folder_name = payload.get("html_folder")

    if not title or not token or not html_folder_name:
        raise ValidationFailed(
            code="MISSING_REQUIRED_FIELDS",
            message="project_name, token, and html_folder are required.",
        )

    html_folder = os.path.join("data", "htmls", html_folder_name)
    if not os.path.isdir(html_folder):
        raise NotFound(
            code="HTML_FOLDER_NOT_FOUND",
            message="HTML folder not found.",
        )

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    # Fetch projects
    try:
        r = requests.get(f"{LABEL_STUDIO_URL}/api/projects", headers=headers, timeout=30)
        r.raise_for_status()
    except requests.RequestException:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Could not load projects from Label Studio.",
        )

    projects_json = r.json()
    projects = (
        projects_json
        if isinstance(projects_json, list)
        else projects_json.get("projects") or projects_json.get("results") or []
    )
    project_id = next((p["id"] for p in projects if p.get("title") == title), None)

    if not project_id:
        raise NotFound(
            code="PROJECT_NOT_FOUND",
            message="Project not found in Label Studio.",
        )

    tasks = collect_html_tasks(html_folder)

    if tasks:
        upload_in_batches(tasks, BATCH_SIZE, project_id, headers)

    return {"status": "ok"}
