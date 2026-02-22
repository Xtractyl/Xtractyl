# orchestrator/routes/utils/shared/label_studio_client.py
import os
from typing import List, Tuple

import requests
from domain.errors import ExternalServiceError, NotFound
from requests.exceptions import HTTPError

LABEL_STUDIO_URL = os.getenv(
    "LABEL_STUDIO_URL",
    f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:{os.getenv('LABELSTUDIO_PORT', '8080')}",
)


def list_projects(token: str) -> list[dict]:
    url = f"{LABEL_STUDIO_URL}/api/projects"
    try:
        r = requests.get(url, headers=_auth_headers(token), timeout=20)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Label Studio is unavailable.",
        )
    return data.get("results", data) if isinstance(data, dict) else data


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


def resolve_project_id(token: str, project_name: str) -> int:
    url = f"{LABEL_STUDIO_URL}/api/projects"
    try:
        r = requests.get(url, headers=_auth_headers(token), timeout=20)
        r.raise_for_status()
        projects = r.json()
    except HTTPError as e:
        status = getattr(e.response, "status_code", None)
        if status in (401, 403):
            raise ExternalServiceError(
                code="LABEL_STUDIO_UNAUTHORIZED",
                message="Label Studio token is invalid or unauthorized.",
            )
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Label Studio is unavailable.",
        )
    except requests.RequestException:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Label Studio is unavailable.",
        )
    if isinstance(projects, dict) and "results" in projects:
        projects = projects["results"]
    for p in projects:
        if p.get("title") == project_name:
            return int(p["id"])
    raise NotFound(
        code="PROJECT_NOT_FOUND",
        message=f'Project "{project_name}" not found.',
        meta={"project_name": project_name},
    )


def get_project(token: str, project_id: int) -> dict:
    url = f"{LABEL_STUDIO_URL}/api/projects/{int(project_id)}"
    try:
        r = requests.get(url, headers=_auth_headers(token), timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Label Studio is unavailable.",
        )


def fetch_tasks_page(token: str, project_id: int) -> Tuple[List[dict], int]:
    """
    Fetch all tasks (including predictions) for a project — without pagination.
    Works for both dict and list responses from Label Studio.
    """
    headers = _auth_headers(token)
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks"
    params = {"fields": "all", "include": "predictions,annotations"}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Label Studio is unavailable.",
        )

    if isinstance(data, dict) and "results" in data:
        tasks = data.get("results", [])
        total = int(data.get("count", len(tasks)))
    elif isinstance(data, list):
        tasks = data
        total = len(tasks)
    else:
        tasks = []
        total = 0

    return tasks, total


def fetch_task_annotations(token: str, task_id: int) -> List[dict]:
    url = f"{LABEL_STUDIO_URL}/api/tasks/{task_id}/annotations"
    try:
        r = requests.get(url, headers=_auth_headers(token), timeout=30)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException:
        raise ExternalServiceError(
            code="LABEL_STUDIO_UNAVAILABLE",
            message="Label Studio is unavailable.",
        )
    return data if isinstance(data, list) else []
