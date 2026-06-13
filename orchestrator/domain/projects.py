# orchestrator/domain/projects.py
import json
import os

import requests
from infrastructure.interfaces.label_studio import LabelStudioInterface
from infrastructure.interfaces.repository import ProjectRepositoryInterface
from infrastructure.interfaces.storage import StorageInterface

from domain.errors import (
    DomainError,
    ExternalServiceError,
    InternalError,
    InvalidState,
    NotFound,
    ValidationFailed,
)
from domain.models.projects import (
    CreateProjectCommand,
    ListQalJsonsCommand,
    PreviewQalCommand,
    ProjectExistsCommand,
    UploadTasksCommand,
)

# Fixed base dir (no env lookups)
BASE_PROJECTS_DIR = os.path.join("data", "projects")

BATCH_SIZE = 50

USE_DB_BACKEND = os.getenv("USE_DB_BACKEND", "0") == "1"

LABELSTUDIO_HOST = os.getenv("LABELSTUDIO_CONTAINER_NAME", "labelstudio")
LABELSTUDIO_PORT = os.getenv("LABELSTUDIO_PORT", "8080")
LABEL_STUDIO_URL = f"http://{LABELSTUDIO_HOST}:{LABELSTUDIO_PORT}"


def check_project_exists(cmd: ProjectExistsCommand, repo: ProjectRepositoryInterface):
    try:
        if USE_DB_BACKEND:
            if repo.project_exists(cmd.project):
                raise InvalidState(
                    code="PROJECT_ALREADY_EXISTS",
                    message="A project with this name already exists.",
                )
            return {"exists": False}

        project = cmd.project
        project_path = os.path.join("data", "projects", project)
        gt_path = os.path.join("data", "projects", "Evaluation_Sets_Do_Not_Delete", project)
        exists = os.path.exists(project_path) or os.path.exists(gt_path)

        if exists:
            raise InvalidState(
                code="PROJECT_ALREADY_EXISTS",
                message="A project with this name already exists.",
            )
        return {"exists": False}
    except DomainError:
        raise
    except Exception:
        raise InternalError(
            code="INTERNAL_ERROR",
            message="Could not check if project exists.",
        )


def create_project_main_from_payload(
    cmd: CreateProjectCommand, repo: ProjectRepositoryInterface, label_studio: LabelStudioInterface
):
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

    if not USE_DB_BACKEND:
        base_path = os.path.join("data", "projects", title)
        os.makedirs(base_path, exist_ok=True)
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

    project_id = label_studio.create_project(title, label_config, token)
    label_studio.attach_ml_backend(project_id, token)

    if USE_DB_BACKEND:
        repo.set_label_studio_id(title, project_id)
        repo.save_questions_and_labels(title, {"questions": questions, "labels": labels})

    return {"project_id": project_id}


def list_projects_ready_for_upload(repo: ProjectRepositoryInterface):
    if USE_DB_BACKEND:
        projects = repo.get_projects_ready_for_upload()
        return {"projects": [p.name for p in projects]}
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
        return {"projects": subfolders}
    except Exception:
        raise InternalError(
            code="INTERNAL_ERROR",
            message="Could not list HTML subfolders.",
        )


def _safe_join(base: str, *paths: str) -> str:
    """Prevent path traversal by resolving and checking commonprefix."""
    full = os.path.abspath(os.path.join(base, *paths))
    base_abs = os.path.abspath(base)
    if not full.startswith(base_abs + os.sep):
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


def preview_qal(cmd: PreviewQalCommand, repo: ProjectRepositoryInterface):
    try:
        if USE_DB_BACKEND:
            qal = repo.get_questions_and_labels(cmd.project)
            if not qal:
                raise NotFound(
                    code="QAL_NOT_FOUND",
                    message="No QAL found for this project.",
                )
            return {"data": qal}

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


def upload_tasks_main_from_payload(
    cmd: UploadTasksCommand,
    repo: ProjectRepositoryInterface,
    storage: StorageInterface,
    label_studio: LabelStudioInterface,
):
    if USE_DB_BACKEND:
        label_studio_id = repo.get_label_studio_id(cmd.project)
        if not label_studio_id:
            raise NotFound(
                code="PROJECT_NOT_FOUND",
                message="Project not found or has no Label Studio ID.",
            )
        html_keys = repo.get_html_keys_for_project(cmd.project)
        if not html_keys:
            raise NotFound(
                code="NO_HTML_FILES",
                message="No converted HTML files found for this project.",
            )
        tasks = [
            {"data": {"html": storage.get_object(key), "name": os.path.basename(key)}}
            for key in html_keys
        ]
        label_studio.upload_tasks(label_studio_id, tasks, cmd.token)
        repo.set_ls_tasks_uploaded(cmd.project)
        return {"status": "ok"}
    title = cmd.project
    html_folder_name = cmd.html_folder
    token = cmd.token
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
