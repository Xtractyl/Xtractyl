# orchestrator/domain/evaluation_drift.py

import json
import os
from pathlib import Path

from domain.models.evaluation_drift import GetEvaluationDriftCommand

from .utils.evaluate_project_utils import SPECIAL_PROJECT_TITLE

LOGS_DIR = Path(os.getenv("LOGS_DIR", "/logs"))
EVAL_LOG_PATH = LOGS_DIR / "evaluation_over_time.jsonl"


def get_evaluation_drift(cmd: GetEvaluationDriftCommand) -> dict:
    """
    Read logs/evaluation_over_time.jsonl and return entries for the standard evaluation series.
    """
    series = SPECIAL_PROJECT_TITLE

    if not EVAL_LOG_PATH.exists():
        return {"series": series, "entries": []}

    entries: list[dict] = []
    with EVAL_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            if obj.get("series") == series:
                entries.append(obj)

    return {"series": series, "entries": entries}
