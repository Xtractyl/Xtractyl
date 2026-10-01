# orchestrator/domain/jobs.py
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

import redis
from infrastructure.interfaces.repository import (
    ModelRepositoryInterface,
    PrelabellingRunRepositoryInterface,
    ProjectRepositoryInterface,
)
from sqlalchemy.exc import IntegrityError
from utils.hashing import compute_system_prompt_hash

from domain.errors import AlreadyExists, InvalidState, NotFound
from domain.models.jobs import (
    CancelJobCommand,
    EnqueueJobCommand,
    JobStatusCommand,
    PrelabelCallbackCommand,
    TaskPrelabellingMetaCommand,
    TaskResultCommand,
)

REDIS_HOST = os.getenv("REDIS_HOST", "job_queue")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

QUEUE = "prelabel_jobs"
STATUS = "status:"
RESULT = "result:"
LOGS = "logs:"

# enqueue_prelabel_job will not be allowed for "pending", "running", "done" status
# it remains allowed for "cancelled", "failed", "incomplete", this allows to finish exactly 1 run
BLOCKING_RUN_STATES = ("pending", "running", "done")


def _status_key(job_id: str) -> str:
    return f"{STATUS}{job_id}"


def _result_key(job_id: str) -> str:
    return f"{RESULT}{job_id}"


def _logs_key(job_id: str) -> str:
    return f"{LOGS}{job_id}"


def get_job_status(cmd: JobStatusCommand):
    job_id = cmd.job_id
    h = r.hgetall(_status_key(job_id)) or {}
    if not h:
        return {"job_id": job_id, "state": "NOT_FOUND"}
    res = r.get(_result_key(job_id))
    out: Dict[str, Any] = {"job_id": job_id, **h}
    if res:
        try:
            out["result"] = json.loads(res)
        except Exception:
            out["result"] = res
    return out


def enqueue_prelabel_job(
    cmd: EnqueueJobCommand,
    run_repo: PrelabellingRunRepositoryInterface,
    project_repo: ProjectRepositoryInterface,
    model_repo: ModelRepositoryInterface,
) -> Dict[str, Any]:
    label_studio_id = project_repo.get_label_studio_id(cmd.project_name)
    if not label_studio_id:
        raise NotFound(
            code="PROJECT_NOT_FOUND",
            message="Project not found or has no Label Studio ID.",
        )
    if not project_repo.get_questions_and_labels(cmd.project_name):
        raise NotFound(
            code="QAL_NOT_FOUND",
            message="No QAL found for this project.",
        )
    if not project_repo.tasks_already_uploaded(cmd.project_name):
        raise InvalidState(
            code="TASKS_NOT_UPLOADED",
            message="Tasks have not been uploaded to Label Studio for this project.",
        )
    existing_run = run_repo.get_run_for_project(cmd.project_name)
    if existing_run and existing_run.status in BLOCKING_RUN_STATES:
        raise AlreadyExists(
            code="PRELABELLING_RUN_ALREADY_EXISTS",
            message=(
                f"A prelabelling run for project '{cmd.project_name}' "
                f"already exists (status '{existing_run.status}')."
            ),
        )
    model = model_repo.get_by_archived_name(cmd.model)
    if not model:
        raise NotFound(code="MODEL_NOT_FOUND", message=f"Unknown model '{cmd.model}'.")

    if existing_run:
        if existing_run.model_id != model.id or (
            existing_run.system_prompt_hash != compute_system_prompt_hash(cmd.system_prompt)
        ):
            original_model = model_repo.get_by_id(existing_run.model_id)
            raise InvalidState(
                code="RESUME_CONFIG_MISMATCH",
                message=(
                    f"The run for project '{cmd.project_name}' ended as '{existing_run.status}' "
                    "and can only be resumed with its original configuration.\n"
                    f"Model: {original_model.archived_name}\n"
                    f"System prompt:\n{existing_run.system_prompt}"
                ),
            )

        if not run_repo.resume_run(existing_run.id):
            raise AlreadyExists(
                code="PRELABELLING_RUN_ALREADY_EXISTS",
                message=(
                    f"The prelabelling run for project '{cmd.project_name}' "
                    "is already being resumed."
                ),
            )
        job_id = str(existing_run.id)
    else:
        try:
            job_id = str(
                run_repo.create_run(
                    project=cmd.project_name,
                    model_id=model.id,
                    system_prompt=cmd.system_prompt,
                )
            )
        except IntegrityError as e:
            # UniqueConstraint on "project" in PrelabellingRun: catches two concurrent first
            # enqueues that both saw no existing run. Translated here from a raw DB error.
            raise AlreadyExists(
                code="PRELABELLING_RUN_ALREADY_EXISTS",
                message=(f"A prelabelling run already exists for project '{cmd.project_name}'."),
            ) from e

        html_keys = project_repo.get_html_keys_for_project(cmd.project_name)
        run_repo.create_run_tasks(int(job_id), [os.path.basename(key) for key in html_keys])

    r.hset(
        _status_key(job_id),
        mapping={
            "state": "PENDING",
            "progress": "0",
            "project_name": cmd.project_name,
            "model": cmd.model,
            "created_at": str(time.time()),
            "error": "",
        },
    )
    r.delete(_result_key(job_id))
    r.delete(_logs_key(job_id))

    payload = {
        "job_id": job_id,
        "project_name": cmd.project_name,
        "label_studio_id": label_studio_id,
        "model": cmd.model,
        "system_prompt": cmd.system_prompt,
        "questions_and_labels": cmd.questions_and_labels,
        "token": cmd.token,
    }
    r.rpush(QUEUE, json.dumps(payload))

    return {
        "job_id": job_id,
        "status_url": f"/prelabel/status/{job_id}",
        "cancel_url": f"/prelabel/cancel/{job_id}",
    }


def cancel_prelabel_job(cmd: CancelJobCommand) -> Dict[str, Any]:
    job_id = cmd.job_id
    r.hset(_status_key(job_id), "state", "CANCEL_REQUESTED")
    return {"job_id": job_id, "status": "cancel_requested"}


def handle_prelabel_callback(
    cmd: PrelabelCallbackCommand,
    run_repo: PrelabellingRunRepositoryInterface,
    project_repo: ProjectRepositoryInterface,
    eval_repo,
) -> dict:
    run_repo.set_run_status(int(cmd.job_id), cmd.status, cmd.error)
    if cmd.status == "done":
        # Trigger A: check every existing groundtruth set for a match now
        # that this run's predictions are final. Imported here rather than
        # at module level to avoid a jobs.py <-> evaluation.py import cycle
        # (evaluation.py does not import from jobs.py, so this is one-way).
        from domain.evaluation import sync_missing_evaluations

        sync_missing_evaluations(project_repo=project_repo, run_repo=run_repo, eval_repo=eval_repo)
    return {"status": "ok"}


def handle_task_prelabelling_meta(
    cmd: TaskPrelabellingMetaCommand,
    run_repo: PrelabellingRunRepositoryInterface,
) -> dict:
    run = run_repo.get_run(cmd.job_id)
    if not run:
        raise NotFound(
            code="RUN_NOT_FOUND",
            message=f"No prelabelling run with id {cmd.job_id}.",
        )
    run_repo.save_task_prelabelling_meta(
        prelabelling_run_id=cmd.job_id,
        label_studio_task_id=cmd.task_id,
        filename=cmd.filename,
        predictions=cmd.predictions,
        raw_llm_answers=cmd.raw_llm_answers,
        dom_match_diagnostics=cmd.dom_match_diagnostics,
        dom_match_by_label=cmd.dom_match_by_label,
        task_ms_total=cmd.task_ms_total,
        task_ms_llm_total=cmd.task_ms_llm_total,
        task_ms_dom_extract=cmd.task_ms_dom_extract,
        task_ms_dom_match=cmd.task_ms_dom_match,
        n_llm_calls=cmd.n_llm_calls,
        n_timeouts=cmd.n_timeouts,
        avg_llm_call_ms=cmd.avg_llm_call_ms,
        median_llm_call_ms=cmd.median_llm_call_ms,
    )
    return {"status": "ok"}


def handle_task_result(
    cmd: TaskResultCommand,
    run_repo: PrelabellingRunRepositoryInterface,
) -> dict:
    run = run_repo.get_run(cmd.job_id)
    if not run:
        raise NotFound(
            code="RUN_NOT_FOUND",
            message=f"No prelabelling run with id {cmd.job_id}.",
        )
    found = run_repo.save_run_task_result(
        prelabelling_run_id=cmd.job_id,
        filename=cmd.filename,
        label_studio_task_id=cmd.task_id,
        status="success" if cmd.success else "failed",
        error=None if cmd.success else cmd.error,
        predictions=cmd.predictions,
        raw_llm_answers=cmd.raw_llm_answers,
        dom_match_diagnostics=cmd.dom_match_diagnostics,
        dom_match_by_label=cmd.dom_match_by_label,
        task_ms_total=cmd.task_ms_total,
        task_ms_llm_total=cmd.task_ms_llm_total,
        task_ms_dom_extract=cmd.task_ms_dom_extract,
        task_ms_dom_match=cmd.task_ms_dom_match,
        n_llm_calls=cmd.n_llm_calls,
        n_timeouts=cmd.n_timeouts,
        avg_llm_call_ms=cmd.avg_llm_call_ms,
        median_llm_call_ms=cmd.median_llm_call_ms,
    )
    if not found:
        raise NotFound(
            code="RUN_TASK_NOT_FOUND",
            message=f"No task '{cmd.filename}' in prelabelling run {cmd.job_id}.",
        )
    run_repo.mark_run_running(cmd.job_id)
    return {"status": "ok"}
