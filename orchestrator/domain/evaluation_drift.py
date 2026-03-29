# orchestrator/domain/evaluation_drift.py

import json
import os
from pathlib import Path

from domain.evaluation import GROUNDTRUTH_QAL_DIR
from domain.models.evaluation_drift import GetEvaluationDriftCommand

DRIFT_DIR = Path(os.getenv("DRIFT_DIR", "/app/data/evaluation_drift"))
EVAL_LOG_PATH = DRIFT_DIR / "evaluation_over_time.jsonl"


def get_evaluation_drift(cmd: GetEvaluationDriftCommand) -> dict:
    """
    Read evaluation_over_time.jsonl from the drift directory and return all entries grouped by GT set.

    Args:
        cmd: GetEvaluationDriftCommand (currently unused, reserved for future filtering).

    Returns:
        {"sets": [{"series": str, "entries": list[dict]}]}
    """
    known_series = (
        {
            p.name
            for p in GROUNDTRUTH_QAL_DIR.iterdir()
            if p.is_dir() and (p / "questions_and_labels.json").is_file()
        }
        if GROUNDTRUTH_QAL_DIR.is_dir()
        else set()
    )

    if not EVAL_LOG_PATH.exists():
        return {"sets": [{"series": s, "entries": []} for s in sorted(known_series)]}

    by_series: dict[str, list[dict]] = {}
    with EVAL_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            series = obj.get("series")
            if series in known_series:
                by_series.setdefault(series, []).append(obj)

    return {"sets": [{"series": s, "entries": by_series.get(s, [])} for s in sorted(known_series)]}
