# worker/domain/prelabel_project.py
from __future__ import annotations

import time

from contracts.jobs import JobPayload
from infrastructure.label_studio import get_tasks_without_predictions
from infrastructure.ml_backend import send_predict
from infrastructure.orchestrator import send_task_result
from utils.logging_utils import dev_logger, safe_logger


def prelabel_project(job: JobPayload) -> None:
    """Process all open tasks of the job's project.
    Stops early if the orchestrator answers a task result with continue=false (run cancelled).
    """
    safe_logger.info(
        "prelabel_started | job_id=%s | label_studio_id=%s", job.job_id, job.label_studio_id
    )
    if dev_logger:
        dev_logger.info(
            "prelabel_started_dev | job_id=%s | project=%s", job.job_id, job.project_name
        )

    tasks = get_tasks_without_predictions(job.label_studio_id, job.token)
    safe_logger.info("prelabel_tasks_found | job_id=%s | count=%s", job.job_id, len(tasks))

    durations: list[float] = []

    for t in tasks:
        task_id = t["id"]
        html = (t.get("data") or {}).get("html")
        filename = (t.get("data") or {}).get("name", "")
        if not html:
            safe_logger.warning("task_no_html | job_id=%s | task_id=%s", job.job_id, task_id)
            keep_going = send_task_result(
                job_id=job.job_id,
                task_id=task_id,
                filename=filename,
                success=False,
                error="Task has no HTML.",
                result=None,
            )
            if not keep_going:
                safe_logger.info("prelabel_stopped | job_id=%s", job.job_id)
                return
            continue

        start = time.time()
        resp = send_predict(task_id=task_id, html=html, filename=filename, job=job)
        ok = resp.status_code == 200
        if not ok:
            safe_logger.warning(
                "predict_rejected | job_id=%s | task_id=%s | status=%s",
                job.job_id,
                task_id,
                resp.status_code,
            )
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
        safe_logger.info(
            "task_finished | job_id=%s | task_id=%s | seconds=%s | status=%s",
            job.job_id,
            task_id,
            round(dt, 2),
            "ok" if ok else "failed",
        )
        if not keep_going:
            safe_logger.info("prelabel_stopped | job_id=%s", job.job_id)
            return

    if durations:
        total_time = sum(durations)
        safe_logger.info(
            "prelabel_summary | job_id=%s | tasks=%s | total_s=%s | avg_s=%s",
            job.job_id,
            len(durations),
            round(total_time, 2),
            round(total_time / len(durations), 2),
        )
