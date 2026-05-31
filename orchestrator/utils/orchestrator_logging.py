# orchestrator/utils/orchestrator_logging.py
from __future__ import annotations

import json
import os
import pathlib
from datetime import datetime
from typing import Any

DEBUG_ARTIFACTS = os.getenv("DEBUG_ARTIFACTS", "0") == "1"

FIXTURES_DIR = pathlib.Path(os.getenv("FIXTURES_DIR", "/app/data/fixtures"))
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

DRIFT_DIR = pathlib.Path(os.getenv("DRIFT_DIR", "/app/data/evaluation_drift"))
DRIFT_DIR.mkdir(parents=True, exist_ok=True)
EVAL_OVER_TIME_LOG = DRIFT_DIR / "evaluation_over_time.jsonl"

CAPTURE_FIXTURES = os.getenv("CAPTURE_FIXTURES", "0") == "1"
SYNTHETIC_DATA = os.getenv("SYNTHETIC_DATA", "0") == "1"


def write_fixture(filename: str, data: str | bytes) -> pathlib.Path | None:
    if not (DEBUG_ARTIFACTS and CAPTURE_FIXTURES and SYNTHETIC_DATA):
        return None
    path = FIXTURES_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data)
    return path


def log_evaluation_over_time(event: dict[str, Any]) -> pathlib.Path:
    safe_event = {"ts": datetime.utcnow().isoformat(timespec="seconds") + "Z", **event}
    with EVAL_OVER_TIME_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe_event, ensure_ascii=False, separators=(",", ":")) + "\n")
    return EVAL_OVER_TIME_LOG
