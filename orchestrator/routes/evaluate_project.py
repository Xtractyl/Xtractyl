# orchestrator/routes/evaluate_project.py

import os

import requests

LABEL_STUDIO_URL = (
    f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:"
    f"{os.getenv('LABELSTUDIO_PORT', '8080')}"
)


def _auth_headers(token: str) -> dict:
    """
    Simple auth header generator.
    If you have a shared version, replace this import accordingly.
    """
    return {"Authorization": f"Token {token}"}


def list_project_names(token: str) -> list[str]:
    """
    Return a list of Label Studio project titles for the given token.
    """
    url = f"{LABEL_STUDIO_URL}/api/projects"
    r = requests.get(url, headers=_auth_headers(token), timeout=20)
    r.raise_for_status()

    projects = r.json()
    if isinstance(projects, dict) and "results" in projects:
        projects = projects["results"]

    return [p.get("title") for p in projects if p.get("title")]


def _resolve_project_id(token: str, project_name: str) -> int:
    """
    Resolve the Label Studio project ID for a project name.
    """
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


def evaluate_projects(token: str, groundtruth_project: str, comparison_project: str) -> dict:
    """
    Resolve project IDs and (später) compute evaluation metrics.
    Aktuell nur Stub / Platzhalter.
    """
    gt_id = _resolve_project_id(token, groundtruth_project)
    cmp_id = _resolve_project_id(token, comparison_project)

    # TODO: hier später Tasks/Annotations laden und Metriken berechnen
    return {
        "groundtruth_project": groundtruth_project,
        "groundtruth_project_id": gt_id,
        "comparison_project": comparison_project,
        "comparison_project_id": cmp_id,
        "overall_metrics": {},
        "task_metrics": [],
        "answer_comparison": [],
    }
