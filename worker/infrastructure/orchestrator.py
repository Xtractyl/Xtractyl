# worker/infrastructure/orchestrator.py
from __future__ import annotations

import os

import requests
from contracts.jobs import JobPayload
from utils.logging_utils import dev_logger, safe_logger

ORCH_HOST = os.getenv("ORCH_CONTAINER_NAME", "orchestrator")
ORCH_PORT = os.getenv("ORCH_PORT", "5001")
ORCHESTRATOR_URL = f"http://{ORCH_HOST}:{ORCH_PORT}"


def send_task_meta(*, task_id: int, meta: dict, job: JobPayload) -> None:
    payload = {
        "job_id": job.job_id,
        "task_id": task_id,
        "filename": meta.get("filename", ""),
        "predictions": meta.get("predictions", []),
        "raw_llm_answers": meta.get("raw_llm_answers", {}),
        "dom_match_diagnostics": meta.get("dom_match_diagnostics", []),
        "dom_match_by_label": meta.get("dom_match_by_label", {}),
        "task_ms_total": meta.get("task_ms_total", 0.0),
        "task_ms_llm_total": meta.get("task_ms_llm_total", 0.0),
        "task_ms_dom_extract": meta.get("task_ms_dom_extract", 0.0),
        "task_ms_dom_match": meta.get("task_ms_dom_match", 0.0),
        "n_llm_calls": meta.get("n_llm_calls", 0),
        "n_timeouts": meta.get("n_timeouts", 0),
        "avg_llm_call_ms": meta.get("avg_llm_call_ms", 0.0),
        "median_llm_call_ms": meta.get("median_llm_call_ms", 0.0),
    }
    if dev_logger:
        dev_logger.info("send_task_meta_payload | task_id=%s | payload=%s", task_id, payload)
    try:
        resp = requests.post(
            f"{ORCHESTRATOR_URL}/prelabel/task-meta",
            json=payload,
            timeout=10,
        )
        if resp.status_code != 200:
            safe_logger.error(
                "send_task_meta_rejected | job_id=%s | task_id=%s | status=%s",
                job.job_id,
                task_id,
                resp.status_code,
            )
            if dev_logger:
                dev_logger.error("send_task_meta_rejected_dev | body=%s", resp.text)
    except requests.RequestException as e:
        safe_logger.error("send_task_meta_failed | job_id=%s | task_id=%s", job.job_id, task_id)
        if dev_logger:
            dev_logger.exception("send_task_meta_failed_dev | error=%s", str(e))
