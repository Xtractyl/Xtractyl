# worker/utils/prelabel_utils.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests

LS_HOST = os.getenv("LS_HOST", "labelstudio")
LS_PORT = int(os.getenv("LS_PORT", "8080"))
LS_BASE = os.getenv("LS_BASE", f"http://{LS_HOST}:{LS_PORT}")

ML_HOST = os.getenv("ML_BACKEND_HOST", "ml_backend")
ML_PORT = int(os.getenv("ML_BACKEND_PORT", "6789"))
ML_BASE = os.getenv("ML_BACKEND_BASE", f"http://{ML_HOST}:{ML_PORT}")

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30"))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2"))
POLL_TIMEOUT = float(os.getenv("POLL_TIMEOUT", "900"))

PAGE_SIZE = int(os.getenv("LS_PAGE_SIZE", "100"))


def _ls_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Token {token}", "Content-Type": "application/json"}


def resolve_project_id_by_title(project_title: str, token: str) -> int:
    url = f"{LS_BASE}/api/projects"
    params = {"page_size": PAGE_SIZE}
    headers = _ls_headers(token)

    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", data if isinstance(data, list) else [])
        for proj in results:
            title = proj.get("title") or proj.get("name")
            if title == project_title:
                pid = proj.get("id")
                if not isinstance(pid, int):
                    raise ValueError(f"Project id is not int: {pid}")
                return pid

        next_url = data.get("next")
        if next_url:
            url = next_url
            params = None
        else:
            break

    raise ValueError(f"Project not found by title: {project_title}")


def _list_tasks_page(
    project_id: int, token: str, page: int = 1, page_size: int = PAGE_SIZE
) -> Dict[str, Any]:
    url = f"{LS_BASE}/api/projects/{project_id}/tasks"
    headers = _ls_headers(token)
    params = {
        "page": page,
        "page_size": page_size,
        "include": "predictions",
        "fields": "id,data,predictions",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_tasks_without_predictions(
    project_id: int, token: str, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    page = 1
    seen = 0

    while True:
        data = _list_tasks_page(project_id, token, page=page, page_size=PAGE_SIZE)

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


def send_predict(
    *,
    task_id: int,
    html: str,
    job_id: str,
    model: str,
    system_prompt: str,
    token: str,
    questions_and_labels: Any,
) -> requests.Response:
    url = f"{ML_BASE}/predict"

    questions_list = labels_list = None
    if isinstance(questions_and_labels, dict):
        questions_list = questions_and_labels.get("questions")
        labels_list = questions_and_labels.get("labels")

    payload: Dict[str, Any] = {
        "task_id": task_id,
        "html": html,
        "job_id": job_id,
        "model": model,
        "system_prompt": system_prompt,
        "token": token,
        "questions_and_labels": questions_and_labels,  # back-compat
        "params": {
            "label_studio_url": LS_BASE,
            "ls_token": token,
            "ollama_model": model,
            "ollama_base": os.getenv("OLLAMA_BASE", "http://ollama:11434"),
            "system_prompt": system_prompt,
            "llm_timeout_seconds": int(os.getenv("LLM_TIMEOUT", "20")),
        },
    }
    if questions_list is not None:
        payload["questions"] = questions_list
    if labels_list is not None:
        payload["labels"] = labels_list

    return requests.post(url, json=payload, timeout=HTTP_TIMEOUT)


def _task_has_predictions(task: Dict[str, Any]) -> bool:
    preds = task.get("predictions") or []
    return len(preds) > 0


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
