# worker/domain/prelabel_project.py
from __future__ import annotations

import time
from typing import Callable, List, Optional

from contracts.jobs import JobPayload
from infrastructure.label_studio import get_tasks_without_predictions
from infrastructure.ml_backend import send_predict
from infrastructure.orchestrator import send_task_meta, send_task_result

LogCB = Optional[Callable[[str], None]]
ProgressCB = Optional[Callable[[int], None]]


def prelabel_project(
    job: JobPayload,
    log_cb: LogCB = None,
    progress_cb: ProgressCB = None,
) -> tuple[List[str], bool]:

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

    _log(f"[INFO] Using project '{job.project_name}' (id={job.label_studio_id}).")

    tasks = get_tasks_without_predictions(job.label_studio_id, job.token)
    total = len(tasks)
    _log(f"[INFO] Found {total} tasks without predictions.")

    total_time = 0.0
    durations: List[float] = []
    done = 0
    stopped = False

    _progress(0 if total > 0 else 100)

    for t in tasks:
        task_id = t["id"]
        html = (t.get("data") or {}).get("html")
        filename = (t.get("data") or {}).get("name", "")
        if not html:
            _log(f"[WARN] Task {task_id} has no HTML. Skipping.")
            keep_going = send_task_result(
                job_id=job.job_id,
                task_id=task_id,
                filename=filename,
                success=False,
                error="Task has no HTML.",
                result=None,
            )
            done += 1
            _progress(int(done / total * 100) if total else 100)
            if not keep_going:
                _log("[INFO] Stopped by the orchestrator (run cancelled).")
                stopped = True
                break
            continue

        start = time.time()
        resp = send_predict(task_id=task_id, html=html, filename=filename, job=job)
        ok = resp.status_code == 200
        if not ok:
            _log(f"[WARN] /predict returned {resp.status_code} for task {task_id}. Continuing.")
            keep_going = send_task_result(
                job_id=job.job_id,
                task_id=task_id,
                filename=filename,
                success=False,
                error=f"/predict returned HTTP {resp.status_code}",
                result=None,
            )
        else:
            body = resp.json()
            meta = body.get("meta", {})
            send_task_meta(task_id=task_id, meta=meta, job=job)
            keep_going = send_task_result(
                job_id=job.job_id,
                task_id=task_id,
                filename=filename,
                success=True,
                error=None,
                result=meta,
            )
        dt = time.time() - start
        durations.append(dt)
        total_time += dt
        status = "ok" if ok else "failed"
        _log(f"[TIME] Task {task_id} finished in {round(dt, 2)}s ({status}).")

        done += 1
        _progress(int(done / total * 100) if total else 100)
        if not keep_going:
            _log("[INFO] Stopped by the orchestrator (run cancelled).")
            stopped = True
            break

    if durations:
        avg = total_time / len(durations)
        _log(
            f"[SUMMARY] Processed: {len(durations)} tasks | Total: {round(total_time, 2)}s | Avg: {round(avg, 2)}s"
        )

    _log(f"[JOB] job_id={job.job_id}")
    return logs, stopped
