# orchestrator/routes/evaluate_project.py

from routes.utils.evaluate_project_utils import (create_evaluation_project, SPECIAL_PROJECT_TITLE)
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
    Resolve project IDs and compute evaluation metrics (future step).
    If the Groundtruth-Projekt 'Evaluation_Set_Do_Not_Delete' does not exist,
    it will be uploaded into labelstudio and resolved afterwards
    """

    # ---- Groundtruth-ID will be resolved ----
    try:
        gt_id = _resolve_project_id(token, groundtruth_project)
    except ValueError:
        if groundtruth_project == SPECIAL_PROJECT_TITLE:
            # if Standard-Eval-Set does not exist it will be uploaded from file
            gt_id = create_evaluation_project(token)
        else:
            # non existent name for any other project raises error
            raise

    # ---- Comparison project does not need the standard groundtruth project
    cmp_id = _resolve_project_id(token, comparison_project)

    # ---- here we will later include metrics calculations then integrated into utils/evaluate_project_utils.py ----
    return {
        "groundtruth_project": groundtruth_project,
        "groundtruth_project_id": gt_id,
        "comparison_project": comparison_project,
        "comparison_project_id": cmp_id,
        "overall_metrics": {},      # fill later
        "task_metrics": [],         # fill later
        "answer_comparison": [],    # fill later
    }