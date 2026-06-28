# orchestrator/domain/evaluation_drift.py

import json
import os
from pathlib import Path

from domain.evaluation import GROUNDTRUTH_QAL_DIR
from domain.models.evaluation_drift import GetEvaluationDriftCommand

USE_DB_BACKEND = os.getenv("USE_DB_BACKEND", "0") == "1"


DRIFT_DIR = Path(os.getenv("DRIFT_DIR", "/app/data/evaluation_drift"))
EVAL_LOG_PATH = DRIFT_DIR / "evaluation_over_time.jsonl"


def get_evaluation_drift(cmd: GetEvaluationDriftCommand, run_repo=None, project_repo=None) -> dict:
    if USE_DB_BACKEND and run_repo and project_repo:
        return _get_evaluation_drift_db(cmd, run_repo, project_repo)
    return _get_evaluation_drift_legacy(cmd)


def _get_evaluation_drift_db(cmd: GetEvaluationDriftCommand, run_repo, project_repo) -> dict:
    gt_projects = project_repo.list_groundtruth_projects()
    known_series = sorted([p.name for p in gt_projects])

    sets = []
    for series in known_series:
        evaluations = run_repo.get_evaluations_by_groundtruth_project(series)
        entries = []
        for e in evaluations:
            run = run_repo.get_run(e.comparison_prelabelling_run_id)
            qal = (run.questions_and_labels or {}) if run else {}
            entries.append(
                {
                    "series": series,
                    "run_at_raw": e.run_at.isoformat() if e.run_at else None,
                    "groundtruth_project_id": e.id,
                    "comparison_project_id": e.comparison_prelabelling_run_id,
                    "model": run.ollama_model if run else "",
                    "system_prompt": run.system_prompt if run else None,
                    "questions": qal.get("questions"),
                    "labels": qal.get("labels"),
                    "metrics": {
                        "micro": e.metrics_micro,
                        "per_label": e.metrics_per_label,
                        "filenames_count": e.filenames_count,
                    },
                }
            )
        sets.append({"series": series, "entries": entries})

    return {"sets": sets}


def _get_evaluation_drift_legacy(cmd: GetEvaluationDriftCommand) -> dict:
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
