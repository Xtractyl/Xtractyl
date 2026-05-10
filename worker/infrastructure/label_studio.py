# worker/infrastructure/label_studio.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import HTTPError

from worker.domain.errors import ExternalServiceError, NotFound

LS_HOST = os.getenv("LS_HOST", "labelstudio")
LS_PORT = int(os.getenv("LS_PORT", "8080"))
LS_BASE = os.getenv("LS_BASE", f"http://{LS_HOST}:{LS_PORT}")

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30"))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2"))
POLL_TIMEOUT = float(os.getenv("POLL_TIMEOUT", "900"))
PAGE_SIZE = int(os.getenv("LS_PAGE_SIZE", "100"))


def _ls_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Token {token}", "Content-Type": "application/json"}


def resolve_project_id(token: str, project_name: str) -> int:
    url = f"{LS_BASE}/api/projects"
    while True:
        try:
            r = requests.get(
                url,
                headers=_ls_headers(token),
                timeout=HTTP_TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
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
        projects = data if isinstance(data, list) else data.get("results", [])
        for p in projects:
            if p.get("title") == project_name:
                return int(p["id"])
        next_url = data.get("next") if isinstance(data, dict) else None
        if not next_url:
            break
        url = next_url
    raise NotFound(
        code="PROJECT_NOT_FOUND",
        message=f'Project "{project_name}" not found.',
        meta={"project_name": project_name},
    )


def get_tasks_without_predictions(
    project_id: int, token: str, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    page = 1
    seen = 0

    while True:
        url = f"{LS_BASE}/api/projects/{project_id}/tasks"
        headers = _ls_headers(token)
        params = {
            "page": page,
            "page_size": PAGE_SIZE,
            "include": "predictions",
            "fields": "id,data,predictions",
        }
        resp = requests.get(url, headers=headers, params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict):
            if "results" in data:
                batch = data.get("results") or []
                has_more = bool(data.get("next"))
            elif "tasks" in data:
                batch = data.get("tasks") or []
                has_more = len(batch) == PAGE_SIZE
            else:
                batch = []
                has_more = False
        elif isinstance(data, list):
            batch = data
            has_more = len(batch) == PAGE_SIZE
        else:
            batch = []
            has_more = False

        if not batch:
            break

        for t in batch:
            preds = (t or {}).get("predictions") or []
            if len(preds) == 0:
                tasks.append(t)
                seen += 1
                if limit is not None and seen >= limit:
                    return tasks

        if not has_more:
            break
        page += 1

    return tasks


def _task_has_predictions(task: Dict[str, Any]) -> bool:
    return len(task.get("predictions") or []) > 0


def _fetch_task(task_id: int, token: str) -> Dict[str, Any]:
    url = f"{LS_BASE}/api/tasks/{task_id}"
    headers = _ls_headers(token)
    params = {"include": "predictions", "fields": "id,data,predictions"}
    resp = requests.get(url, headers=headers, params=params, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def wait_until_prediction_saved(
    task_id: int,
    token: str,
    timeout_s: float = POLL_TIMEOUT,
    poll_every_s: float = POLL_INTERVAL,
) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            t = _fetch_task(task_id, token)
            if _task_has_predictions(t):
                return True
        except requests.RequestException:
            pass
        time.sleep(poll_every_s)
    return False
