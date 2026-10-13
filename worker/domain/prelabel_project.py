# worker/domain/prelabel_project.py
from __future__ import annotations

import time
from collections import Counter

from contracts.jobs import JobPayload
from infrastructure.label_studio import get_tasks_without_predictions
from infrastructure.ml_backend import predict
from infrastructure.orchestrator import send_task_result
from utils.logging_utils import dev_logger, safe_logger

from domain.errors import ContractViolation, DomainError, ExternalServiceError, InvalidState


def _preview(names: list[str], limit: int = 5) -> str:
    shown = ", ".join(names[:limit])
    return f"{shown} (+{len(names) - limit} more)" if len(names) > limit else shown


def _assert_tasks_match(expected: list[str], tasks: list[dict]) -> None:
    """Open tasks in Postgres must match exactly open tasks in label studio. Any difference
    lets prelabelling fail. The discrepancies between Postgres and labelstudio tasks mean
    either that someone added tasks to labelstudio directly or removed tasks from labelstudio
    directly. The least likely reason for Postgres/labelstudio discrepasncies
    is that a task's result was written to labelstudio but xtractyl crashed before the write to Postgres.
    """
    found = [(t.get("data") or {}).get("name", "") for t in tasks]
    missing = sorted(set(expected) - set(found))
    unexpected = sorted(set(found) - set(expected))
    duplicated = sorted(name for name, n in Counter(found).items() if n > 1)
    if not (missing or unexpected or duplicated):
        return
    parts = []
    if missing:
        parts.append(f"missing in Label Studio: {_preview(missing)}")
    if unexpected:
        parts.append(f"unexpected in Label Studio: {_preview(unexpected)}")
    if duplicated:
        parts.append(f"duplicated in Label Studio: {_preview(duplicated)}")
    raise InvalidState(
        code="TASKS_OUT_OF_SYNC",
        message="Label Studio does not match the open tasks in Xtractyl ("
        + "; ".join(parts)
        + ").",
    )


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
    _assert_tasks_match(job.task_filenames, tasks)
    safe_logger.info("prelabel_tasks_found | job_id=%s | count=%s", job.job_id, len(tasks))

    durations: list[float] = []

    for t in tasks:
        task_id = t["id"]
        data = t.get("data") or {}
        html = data.get("html")
        filename = data.get("name", "")

        start = time.time()
        task_error: DomainError | None = None
        meta = None
        try:
            meta = predict(task_id=task_id, html=html, filename=filename, job=job)
        except (ExternalServiceError, ContractViolation) as e:
            # A problem with this one task: the task fails, the run goes on. The failed tasks are
            # tried again when the run is resumed.
            task_error = e

        if task_error is None:
            keep_going = send_task_result(
                job_id=job.job_id,
                task_id=task_id,
                filename=filename,
                success=True,
                error=None,
                result=meta.model_dump(),
            )
        else:
            safe_logger.warning(
                "task_failed | job_id=%s | task_id=%s",
                job.job_id,
                task_id,
                extra={"code": task_error.code},
            )
            if dev_logger:
                dev_logger.warning(
                    "task_failed_dev | job_id=%s | task_id=%s | filename=%s",
                    job.job_id,
                    task_id,
                    filename,
                    extra={"code": task_error.code, "meta": task_error.meta},
                )
            keep_going = send_task_result(
                job_id=job.job_id,
                task_id=task_id,
                filename=filename,
                success=False,
                error=str(task_error),
                result=None,
            )
        ok = task_error is None
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
