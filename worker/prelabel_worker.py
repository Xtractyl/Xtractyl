# worker/prelabel_worker.py
from __future__ import annotations

import json
import os
import traceback

import redis

from worker.prelabel_logic import prelabel_complete_project_main

# Redis connection (queue + job state)
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "job_queue"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)

QUEUE = "prelabel_jobs"
STATUS = "status:"
RESULT = "result:"
LOGS = "logs:"


def _status_key(job_id: str) -> str:
    return f"{STATUS}{job_id}"


def _result_key(job_id: str) -> str:
    return f"{RESULT}{job_id}"


def _logs_key(job_id: str) -> str:
    return f"{LOGS}{job_id}"


def _set_status(job_id: str, **kv) -> None:
    r.hset(_status_key(job_id), mapping=kv)


def _get_state(job_id: str) -> str | None:
    return r.hget(_status_key(job_id), "state")


def _add_log(job_id: str, line: str) -> None:
    r.rpush(_logs_key(job_id), line)


def _cancelled(job_id: str) -> bool:
    return _get_state(job_id) == "CANCEL_REQUESTED"


def _mark_cancelled(job_id: str) -> None:
    _set_status(job_id, state="CANCELLED")
    _add_log(job_id, "[INFO] Job cancelled.")


def handle_job(payload: dict) -> None:
    """
    Execute a prelabel job taken from Redis. Supports cancel + progress reporting.
    """
    job_id = payload["job_id"]
    _set_status(job_id, state="RUNNING")
    _add_log(job_id, "[INFO] Worker picked up job.")

    try:
        logs = prelabel_complete_project_main(
            payload,
            log_cb=lambda line: _add_log(job_id, line),
            progress_cb=lambda pct: _set_status(job_id, progress=str(pct)),
            cancel_cb=lambda: _cancelled(job_id),
        )

        # If a cancel was requested at any point, finalize as CANCELLED and stop here.
        if _cancelled(job_id):
            _mark_cancelled(job_id)
            return

        # Persist a small result blob
        r.set(_result_key(job_id), json.dumps({"job_id": job_id, "logs_count": len(logs)}))

        # Do not overwrite terminal states
        final_state = _get_state(job_id) or "RUNNING"
        if final_state not in ("CANCELLED", "FAILED"):
            _set_status(job_id, state="SUCCEEDED", progress="100")

        _add_log(job_id, "[INFO] Job finished.")

    except Exception as e:
        _set_status(job_id, state="FAILED", error=str(e))
        _add_log(job_id, "[ERROR] " + str(e))
        _add_log(job_id, "[TRACEBACK]\n" + traceback.format_exc())


def main() -> None:
    print("[worker] started, waiting for jobs...", flush=True)
    while True:
        item = r.brpop(QUEUE, timeout=5)
        if not item:
            # idle
            continue
        _, raw = item
        try:
            payload = json.loads(raw)
        except Exception:
            print("[worker] invalid payload received, skipping", flush=True)
            continue
        handle_job(payload)


if __name__ == "__main__":
    main()
