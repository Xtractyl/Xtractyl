# orchestrator/routes/utils/shared/label_studio_client.py
import os
from typing import List, Tuple

import requests

LABEL_STUDIO_URL = os.getenv(
    "LABEL_STUDIO_URL",
    f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:{os.getenv('LABELSTUDIO_PORT', '8080')}",
)


def list_projects(token: str) -> list[dict]:
    url = f"{LABEL_STUDIO_URL}/api/projects"
    r = requests.get(url, headers=_auth_headers(token), timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("results", data) if isinstance(data, dict) else data
def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


def resolve_project_id(token: str, project_name: str) -> int:
    url = f"{LABEL_STUDIO_URL}/api/projects"
    r = requests.get(url, headers=_auth_headers(token), timeout=20)
    r.raise_for_status()
    projects = r.json()
    if isinstance(projects, dict) and "results" in projects:
        projects = projects["results"]
    for p in projects:
        if p.get("title") == project_name:
            return int(p["id"])
    raise ValueError(f'Project "{project_name}" not found')


def get_project(token: str, project_id: int) -> dict:
    url = f"{LABEL_STUDIO_URL}/api/projects/{int(project_id)}"
    r = requests.get(url, headers=_auth_headers(token), timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_tasks_page(
    token: str, project_id: int, limit: int = 0, offset: int = 0
) -> Tuple[List[dict], int]:
    """
    Fetch all tasks (including predictions) for a project — without pagination.
    Works for both dict and list responses from Label Studio.
    NOTE: limit/offset currently unused (kept to avoid breaking callers).
    """
    headers = _auth_headers(token)
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks"
    params = {"fields": "all", "include": "predictions,annotations"}

    r = requests.get(url, headers=headers, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()

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
    r = requests.get(url, headers=_auth_headers(token), timeout=30)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []