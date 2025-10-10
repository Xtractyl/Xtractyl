# worker/prelabel_logic.py
from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Callable, List, Optional

from worker.utils.prelabel_utils import (
    get_tasks_without_predictions,
    resolve_project_id_by_title,
    send_predict,
    wait_until_prediction_saved,
)

LogCB = Optional[Callable[[str], None]]
ProgressCB = Optional[Callable[[int], None]]
CancelCB = Optional[Callable[[], bool]]


def prelabel_complete_project_main(
    payload: dict[str, Any],
    log_cb: LogCB = None,
    progress_cb: ProgressCB = None,
    cancel_cb: CancelCB = None,
) -> List[str]:
    """
    Synchronous pre-label run based on explicit payload.

    Required payload keys:
      - project_name: str
      - model: str
      - system_prompt: str
      - qal_file: str
      - token: str
      - (optional) job_id: str
    """
    logs: List[str] = []

    def _log(line: str) -> None:
        logs.append(line)
        if log_cb:
            try:
                log_cb(line)
            except Exception:
                pass  # do not let logging crash the job

    def _progress(pct: int) -> None:
        pct = max(0, min(100, int(pct)))
        if progress_cb:
            try:
                progress_cb(pct)
            except Exception:
                pass
        _log(f"[PROGRESS] {pct}%")

    for k in ("project_name", "model", "system_prompt", "qal_file", "token"):
        if not payload.get(k):
            raise ValueError(f"Missing field: {k}")

    project_name: str = payload["project_name"]
    model: str = payload["model"]
    system_prompt: str = payload["system_prompt"]
    token: str = payload["token"]
    qal_file: str = payload["qal_file"]

    job_id = payload.get("job_id") or f"sync-{uuid.uuid4()}"

    # Load questions & labels (dict with 'questions' and 'labels' arrays).
    qal_path = os.path.join("data", "projects", project_name, qal_file)
    if not os.path.exists(qal_path):
        raise FileNotFoundError(f"Questions & Labels file not found: {qal_path}")
    with open(qal_path, encoding="utf-8") as f:
        questions_and_labels = json.load(f)

    project_id = resolve_project_id_by_title(project_name, token)
    _log(f"[INFO] Using project '{project_name}' (id={project_id}).")

    tasks = get_tasks_without_predictions(project_id, token)
    total = len(tasks)
    _log(f"[INFO] Found {total} tasks without predictions.")

    total_time = 0.0
    durations: List[float] = []
    done = 0

    # initial progress
    _progress(0 if total > 0 else 100)

    for t in tasks:
        if cancel_cb and cancel_cb():
            _log("[INFO] Cancel observed. Stopping.")
            break

        task_id = t["id"]
        html = (t.get("data") or {}).get("html")
        if not html:
            _log(f"[WARN] Task {task_id} has no HTML. Skipping.")
            done += 1
            _progress(int(done / total * 100) if total else 100)
            continue

        start = time.time()
        resp = send_predict(
            task_id=task_id,
            html=html,
            job_id=job_id,
            model=model,
            system_prompt=system_prompt,
            token=token,
            questions_and_labels=questions_and_labels,
        )
        _log(f"[SEND] Task {task_id} → /predict: {resp.status_code}")

        ok = wait_until_prediction_saved(task_id, token)
        dt = time.time() - start
        durations.append(dt)
        total_time += dt
        status = "ok" if ok else "timeout"
        _log(f"[TIME] Task {task_id} finished in {round(dt, 2)}s ({status}).")

        done += 1
        _progress(int(done / total * 100) if total else 100)

    if durations:
        avg = total_time / len(durations)
        _log(
            f"[SUMMARY] Processed: {len(durations)} tasks | Total: {round(total_time, 2)}s | Avg: {round(avg, 2)}s"
        )

    _log(f"[JOB] job_id={job_id}")
    return logs
