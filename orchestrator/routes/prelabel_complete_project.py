# routes/prelabel_complete_project.py
import os
import time
import uuid
import json
from typing import Dict, Any, List

from utils.prelabel_utils import (
    resolve_project_id_by_title,
    get_tasks_without_predictions,
    send_predict,
    wait_until_prediction_saved,
)

def prelabel_complete_project_main(payload: Dict[str, Any]) -> List[str]:
    """
    Synchronous pre-label run based on explicit payload.
    Expected payload:
      - project_name: str
      - model: str
      - system_prompt: str
      - qal_file: str
      - token: str
      - (optional) job_id: str
    """
    logs: List[str] = []
    for k in ("project_name", "model", "system_prompt", "qal_file", "token"):
        if not payload.get(k):
            raise ValueError(f"Missing field: {k}")

    project_name  = payload["project_name"]
    model         = payload["model"]
    system_prompt = payload["system_prompt"]
    token         = payload["token"]
    qal_file      = payload["qal_file"]

    # Job ID (use given or generate)
    job_id = payload.get("job_id") or f"sync-{uuid.uuid4()}"

    # Load Q&A configuration
    qal_path = os.path.join("data", "projects", project_name, qal_file)
    if not os.path.exists(qal_path):
        raise FileNotFoundError(f"Questions & Labels file not found: {qal_path}")
    with open(qal_path, encoding="utf-8") as f:
        questions_and_labels = json.load(f)

    project_id = resolve_project_id_by_title(project_name, token)
    logs.append(f"[INFO] Using project '{project_name}' (id={project_id}).")

    tasks = get_tasks_without_predictions(project_id, token)
    logs.append(f"[INFO] Found {len(tasks)} tasks without predictions.")

    total_time = 0.0
    durations: List[float] = []

    for t in tasks:
        task_id = t["id"]
        html = t.get("data", {}).get("html")
        if not html:
            logs.append(f"[WARN] Task {task_id} has no HTML. Skipping.")
            continue

        start = time.time()
        r = send_predict(
            task_id=task_id,
            html=html,
            job_id=job_id,
            model=model,
            system_prompt=system_prompt,
            token=token,
            questions_and_labels=questions_and_labels,
        )
        logs.append(f"[SEND] Task {task_id} → /predict: {r.status_code}")

        ok = wait_until_prediction_saved(task_id, token)
        dt = time.time() - start
        durations.append(dt)
        total_time += dt
        status = "ok" if ok else "timeout"
        logs.append(f"[TIME] Task {task_id} finished in {round(dt, 2)}s ({status}).")

    if durations:
        avg = total_time / len(durations)
        logs.append(f"[SUMMARY] Processed: {len(durations)} tasks | Total: {round(total_time,2)}s | Avg: {round(avg,2)}s")

    logs.append(f"[JOB] job_id={job_id}")
    return logs