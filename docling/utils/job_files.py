import json
import os
from typing import Any

# Base directory for per-job artifacts
DOC_STATE_DIR = "/logs/docling_jobs"
os.makedirs(DOC_STATE_DIR, exist_ok=True)


def status_path(job_id: str) -> str:
    """Return absolute path to the status JSON file of a job."""
    return os.path.join(DOC_STATE_DIR, f"{job_id}.status.json")


def write_status(job_id: str, **payload: Any) -> None:
    """
    Atomically write the current job status to disk.

    Parameters
    ----------
    job_id : str
        Identifier of the job.
    payload : Any
        Arbitrary serializable key-value pairs describing status.
        Typical keys: state, progress, total, done, message.
    """
    path = status_path(job_id)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, path)  # atomic on POSIX


def read_latest_status(job_id: str) -> dict[str, Any] | None:
    """
    Read the most recent job status from disk.

    Returns
    -------
    dict | None
        Parsed JSON dict if available and valid; None if file does not exist
        or is temporarily unreadable (e.g., mid-write).
    """
    path = status_path(job_id)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
