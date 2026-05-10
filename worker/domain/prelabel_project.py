# worker/domain/prelabel_project.py
from __future__ import annotations

import time
from typing import Callable, List, Optional

from contracts.jobs import JobPayload
from infrastructure.label_studio import (
    get_tasks_without_predictions,
    resolve_project_id,
    wait_until_prediction_saved,
)
from infrastructure.ml_backend import send_predict

LogCB = Optional[Callable[[str], None]]
ProgressCB = Optional[Callable[[int], None]]
CancelCB = Optional[Callable[[], bool]]


def prelabel_project(
    job: JobPayload,
    log_cb: LogCB = None,
    progress_cb: ProgressCB = None,
    cancel_cb: CancelCB = None,
) -> List[str]:
    logs: List[str] = []

    def _log(line: str) -> None:
        logs.append(line)
        if log_cb:
            try:
                log_cb(line)
            except Exception:
                pass

    def _progress(pct: int) -> None:
        pct = max(0, min(100, int(pct)))
        if progress_cb:
            try:
                progress_cb(pct)
            except Exception:
                pass
        _log(f"[PROGRESS] {pct}%")

    project_id = resolve_project_id(job.token, job.project_name)
    _log(f"[INFO] Using project '{job.project_name}' (id={project_id}).")

    tasks = get_tasks_without_predictions(project_id, job.token)
    total = len(tasks)
    _log(f"[INFO] Found {total} tasks without predictions.")

    total_time = 0.0
    durations: List[float] = []
    done = 0

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
        resp = send_predict(task_id=task_id, html=html, job=job)
        _log(f"[SEND] Task {task_id} → /predict: {resp.status_code}")

        ok = wait_until_prediction_saved(task_id, job.token)
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

    _log(f"[JOB] job_id={job.job_id}")
    return logs
