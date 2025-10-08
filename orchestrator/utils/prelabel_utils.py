# utils/prelabel_utils.py
import os
import time
from typing import Any

import requests

# --- Base URLs / ports (read from env, with defaults) ---
LABEL_STUDIO_URL = f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:{os.getenv('LABELSTUDIO_PORT', '8080')}"
ML_BACKEND_URL = f"http://{os.getenv('ML_BACKEND_CONTAINER_NAME', 'ml_backend')}:{os.getenv('ML_BACKEND_PORT', '6789')}"
OLLAMA_BASE = os.getenv(
    "OLLAMA_URL",
    f"http://{os.getenv('OLLAMA_CONTAINER_NAME', 'ollama')}:{os.getenv('OLLAMA_PORT', '11434')}",
)

PAGE_SIZE = 100

__all__ = [
    "LABEL_STUDIO_URL",
    "ML_BACKEND_URL",
    "OLLAMA_BASE",
    "PAGE_SIZE",
    "get_tasks_without_predictions",
    "resolve_project_id_by_title",
    "send_predict",
    "wait_until_prediction_saved",
]


def resolve_project_id_by_title(title: str, token: str) -> int:
    headers = {"Authorization": f"Token {token}"}
    url = f"{LABEL_STUDIO_URL}/api/projects"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    projects = data if isinstance(data, list) else data.get("results") or data.get("projects") or []
    for p in projects:
        if p.get("title") == title:
            return p["id"]
    raise ValueError(f"Project '{title}' not found in Label Studio.")


def get_tasks_without_predictions(project_id: int, token: str) -> list[dict[str, Any]]:
    headers = {"Authorization": f"Token {token}"}
    page = 1
    all_tasks: list[dict[str, Any]] = []
    while True:
        url = (
            f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks?page={page}&page_size={PAGE_SIZE}"
        )
        r = requests.get(url, headers=headers)
        if r.status_code == 404:
            break
        r.raise_for_status()
        page_tasks = r.json()
        if not page_tasks:
            break
        all_tasks.extend(page_tasks)
        page += 1
    return [t for t in all_tasks if not t.get("predictions")]


def send_predict(
    task_id: int,
    html: str,
    job_id: str,
    model: str,
    system_prompt: str,
    token: str,
    questions_and_labels: dict[str, Any],
    llm_timeout_seconds: int = 1200,
):
    payload = {
        "config": {
            "label_studio_url": LABEL_STUDIO_URL,
            "ls_token": token,
            "ollama_model": model,
            "ollama_base": OLLAMA_BASE,
            "system_prompt": system_prompt,
            "llm_timeout_seconds": str(llm_timeout_seconds),  # keep as string to match your backend
        },
        "task": {"id": task_id, "data": {"html": html}},
        "questions_and_labels": questions_and_labels,
    }
    headers = {"X-Prelabel-Job": job_id}
    return requests.post(
        f"{ML_BACKEND_URL}/predict", json=payload, headers=headers, timeout=llm_timeout_seconds
    )


def wait_until_prediction_saved(task_id: int, token: str, timeout: int = 30000) -> bool:
    headers = {"Authorization": f"Token {token}"}
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{LABEL_STUDIO_URL}/api/tasks/{task_id}", headers=headers)
        if r.status_code == 200 and r.json().get("predictions"):
            return True
        time.sleep(1)
    return False
