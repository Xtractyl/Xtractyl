# routes/prelabel_complete_project.py
import time
import requests
import uuid
import os
import json

# --- Base URLs / ports (read from env, with defaults) ---
LABEL_STUDIO_URL = f"http://{os.getenv('LABELSTUDIO_CONTAINER_NAME', 'labelstudio')}:{os.getenv('LABELSTUDIO_PORT', '8080')}"
ML_BACKEND_URL   = f"http://{os.getenv('ML_BACKEND_CONTAINER_NAME', 'ml_backend')}:{os.getenv('ML_BACKEND_PORT', '6789')}"
OLLAMA_BASE = os.getenv("OLLAMA_URL", f"http://{os.getenv('OLLAMA_CONTAINER_NAME', 'ollama')}:{os.getenv('OLLAMA_PORT', '11434')}")

PAGE_SIZE        = 100

def _resolve_project_id_by_title(title: str, token: str) -> int:
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

def _get_tasks_without_predictions(project_id: int, token: str):
    headers = {"Authorization": f"Token {token}"}
    page = 1
    all_tasks = []
    while True:
        url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks?page={page}&page_size={PAGE_SIZE}"
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

def _send_predict(task_id: int, html: str, job_id: str, model: str, system_prompt: str, token: str, questions_and_labels: dict):
    payload = {
        "config": {
            "label_studio_url": LABEL_STUDIO_URL,
            "ls_token": token,
            "ollama_model": model,
            "ollama_base": OLLAMA_BASE,
            "system_prompt": system_prompt,
            "llm_timeout_seconds": "1200" #adapt for long pdfs and slow servers
        },
        "task": {"id": task_id, "data": {"html": html}},
        "questions_and_labels": questions_and_labels
    }
    headers = {"X-Prelabel-Job": job_id}
    return requests.post(f"{ML_BACKEND_URL}/predict", json=payload, headers=headers, timeout=1200)

def _wait_until_prediction_saved(task_id: int, token: str, timeout: int = 30000):
    headers = {"Authorization": f"Token {token}"}
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{LABEL_STUDIO_URL}/api/tasks/{task_id}", headers=headers)
        if r.status_code == 200 and r.json().get("predictions"):
            return True
        time.sleep(1)
    return False

def prelabel_complete_project_main(payload: dict):
    """
    Synchronous pre‑label run based on explicit payload.
    Expected payload:
      - project_name: str
      - model: str
      - system_prompt: str
      - qal_file: str
      - token: str
      - (optional) job_id: str
    """
    logs = []
    for k in ("project_name", "model", "system_prompt", "qal_file", "token"):
        if not payload.get(k):
            raise ValueError(f"Missing field: {k}")

    project_name  = payload["project_name"]
    model         = payload["model"]
    system_prompt = payload["system_prompt"]
    token         = payload["token"]
    qal_file      = payload["qal_file"]

    # NEU: job_id vergeben (oder übergebenen Wert nutzen)
    job_id = payload.get("job_id") or f"sync-{uuid.uuid4()}"

    # NEU: Q&A-Konfiguration aus Datei laden
    qal_path = os.path.join("data", "projects", project_name, qal_file)
    if not os.path.exists(qal_path):
        raise FileNotFoundError(f"Questions & Labels file not found: {qal_path}")
    with open(qal_path, encoding="utf-8") as f:
        questions_and_labels = json.load(f)

    project_id = _resolve_project_id_by_title(project_name, token)
    logs.append(f"[INFO] Using project '{project_name}' (id={project_id}).")

    tasks = _get_tasks_without_predictions(project_id, token)
    logs.append(f"[INFO] Found {len(tasks)} tasks without predictions.")

    total_time = 0.0
    durations = []

    for t in tasks:
        task_id = t["id"]
        html = t.get("data", {}).get("html")
        if not html:
            logs.append(f"[WARN] Task {task_id} has no HTML. Skipping.")
            continue

        start = time.time()
        r = _send_predict(
            task_id, html, job_id=job_id, model=model,
            system_prompt=system_prompt, token=token,
            questions_and_labels=questions_and_labels
        )
        logs.append(f"[SEND] Task {task_id} → /predict: {r.status_code}")

        ok = _wait_until_prediction_saved(task_id, token)
        dt = time.time() - start
        durations.append(dt)
        total_time += dt
        status = "ok" if ok else "timeout"
        logs.append(f"[TIME] Task {task_id} finished in {round(dt, 2)}s ({status}).")

    if durations:
        avg = total_time / len(durations)
        logs.append(f"[SUMMARY] Processed: {len(durations)} tasks | Total: {round(total_time,2)}s | Avg: {round(avg,2)}s")

    # Optional: am Ende die job_id loggen
    logs.append(f"[JOB] job_id={job_id}")

    return logs

