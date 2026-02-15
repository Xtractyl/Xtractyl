# orchestrator/domain/evaluation.py

import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from utils.logging_utils import log_evaluation_over_time, safe_logger

from domain.models.evaluation import EvaluateProjectsCommand

from .utils.calculate_metrics import compute_metrics_from_rows
from .utils.evaluate_project_utils import SPECIAL_PROJECT_TITLE, create_evaluation_project
from .utils.shared.label_studio_client import (
    fetch_task_annotations,
    fetch_tasks_page,
    list_projects,
    resolve_project_id,
)

GROUNDTRUTH_QAL_PATH = os.getenv(
    "GROUNDTRUTH_QAL_PATH",
    "/app/data/projects/Evaluation_Set_Do_Not_Delete/questions_and_labels.json",
)

EVAL_OUT_DIR = Path(os.getenv("EVAL_DIR", "/app/data/evaluation"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _qal_hash_from_file() -> str | None:
    """
    Hash questions+labels for comparability across runs.
    Never logs the QAL content itself.
    """
    try:
        with open(GROUNDTRUTH_QAL_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return _sha256_text(canonical)
    except Exception:
        return None


def _extract_consistent_meta(pred_rows: list[dict]) -> tuple[str | None, str | None]:
    """
    Returns (model, prompt_hash) if consistent across tasks, else (None, None).
    Expects meta keys produced by ml_backend: meta["model"], meta["system_prompt"].
    """
    models: set[str] = set()
    prompt_hashes: set[str] = set()
    for r in pred_rows or []:
        meta = r.get("meta") or {}
        if not isinstance(meta, dict):
            return None, None
        model = meta.get("model")
        if isinstance(model, str) and model.strip():
            models.add(model.strip())
        else:
            # strict: every task must have model
            return None, None
        system_prompt = meta.get("system_prompt")
        if isinstance(system_prompt, str) and system_prompt.strip():
            prompt_hashes.add(_sha256_text(system_prompt))
        else:
            # strict: every task must have prompt
            return None, None
    if len(models) == 1 and len(prompt_hashes) == 1:
        return next(iter(models)), next(iter(prompt_hashes))
    return None, None


def list_project_names(token: str) -> list[str]:
    projects = list_projects(token)
    return [p.get("title") for p in projects if p.get("title")]


def _bucket_from_results(results: list) -> dict:
    """
    Extract {label: text} from LS 'result' list (Labels tool only).
    Single-valued assumption: if multiple, join by ' | '.
    """
    bucket = defaultdict(list)
    for r in results or []:
        if r.get("type") != "labels":
            continue
        val = r.get("value", {}) or {}
        labels = val.get("labels")
        text = val.get("text", "")

        if isinstance(labels, str):
            labels = [labels]
        if not isinstance(labels, list):
            labels = []

        for lab in labels:
            bucket[str(lab)].append(str(text) if text is not None else "")

    return {k: " | ".join(v for v in vs if v is not None) for k, vs in bucket.items()}


def _chosen_annotation_bucket(task: dict) -> dict:
    anns = [a for a in (task.get("annotations") or []) if isinstance(a, dict)]
    if not anns:
        return {}

    gt_anns = [a for a in anns if a.get("ground_truth") is True]
    candidates = gt_anns if gt_anns else anns
    chosen = sorted(
        candidates,
        key=lambda a: a.get("created_at") or a.get("updated_at") or "",
        reverse=True,
    )[0]
    return _bucket_from_results(chosen.get("result") or [])


def _latest_prediction_bucket(task: dict) -> dict:
    preds = [p for p in (task.get("predictions") or []) if isinstance(p, dict)]
    if not preds:
        return {}
    chosen = sorted(
        preds,
        key=lambda p: p.get("created_at") or p.get("updated_at") or "",
        reverse=True,
    )[0]
    return _bucket_from_results(chosen.get("result") or [])


def _latest_prediction_meta(task: dict) -> dict:
    # Prefer prediction.meta if LS returns it; fallback to task.data.ml_meta
    preds = [p for p in (task.get("predictions") or []) if isinstance(p, dict)]
    if preds:
        chosen = sorted(
            preds,
            key=lambda p: p.get("created_at") or p.get("updated_at") or "",
            reverse=True,
        )[0]
        meta = chosen.get("meta")
        if isinstance(meta, dict) and meta:
            return meta

    data = task.get("data") or {}
    ml_meta = data.get("ml_meta")
    return ml_meta if isinstance(ml_meta, dict) else {}


def _write_eval_result(payload: dict, gt_id: int, cmp_id: int) -> str:
    EVAL_OUT_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = EVAL_OUT_DIR / f"eval_gt{gt_id}_cmp{cmp_id}_{ts}.json"

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out_path)


def _tasks_to_rows(token: str, project_id: int, mode: str) -> list[dict]:
    """
    mode='gt'   -> labels from annotations
    mode='pred' -> labels from predictions
    Returns: [{"filename": str, "task_id": int, "labels": {label: text}}]
    """
    tasks, total = fetch_tasks_page(token, project_id)
    rows = []

    for t in tasks:
        data = t.get("data") or {}
        filename = data.get("name", "")

        if mode == "gt":
            anns = t.get("annotations") or []
            if not any(a and (a.get("result") or []) for a in anns):
                t["annotations"] = fetch_task_annotations(token, t.get("id"))
            labels = _chosen_annotation_bucket(t)
        else:
            labels = _latest_prediction_bucket(t)

        meta = _latest_prediction_meta(t) if mode == "pred" else {}

        run_at_raw = None
        if mode == "pred":
            preds = [p for p in (t.get("predictions") or []) if isinstance(p, dict)]
            if preds:
                chosen = sorted(
                    preds,
                    key=lambda p: p.get("created_at") or p.get("updated_at") or "",
                    reverse=True,
                )[0]
                run_at_raw = chosen.get("created_at") or chosen.get("updated_at")

        rows.append(
            {
                "task_id": t.get("id"),
                "filename": filename,
                "labels": labels,
                "meta": meta,
                "run_at_raw": run_at_raw,
            }
        )

    return rows


def evaluate_projects(cmd: EvaluateProjectsCommand) -> dict:
    token = cmd.token
    groundtruth_project = cmd.groundtruth_project
    comparison_project = cmd.comparison_project
    try:
        gt_id = resolve_project_id(token, groundtruth_project)
    except ValueError:
        if groundtruth_project == SPECIAL_PROJECT_TITLE:
            gt_id = create_evaluation_project(token)
        else:
            raise

    cmp_id = resolve_project_id(token, comparison_project)

    gt_rows = _tasks_to_rows(token, gt_id, mode="gt")
    pred_rows = _tasks_to_rows(token, cmp_id, mode="pred")

    gt_set = {r.get("filename") for r in gt_rows if r.get("filename")}
    pr_set = {r.get("filename") for r in pred_rows if r.get("filename")}

    if gt_set != pr_set:
        missing_in_pred = sorted(gt_set - pr_set)
        extra_in_pred = sorted(pr_set - gt_set)
        raise ValueError(
            f"Filename mismatch: missing_in_pred={missing_in_pred[:20]} extra_in_pred={extra_in_pred[:20]}"
        )
    gt_label_set = set()
    for r in gt_rows:
        gt_label_set |= set((r.get("labels") or {}).keys())

    pred_label_set = set()
    for r in pred_rows:
        pred_label_set |= set((r.get("labels") or {}).keys())

    if gt_label_set != pred_label_set:
        missing_in_pred = sorted(gt_label_set - pred_label_set)
        extra_in_pred = sorted(pred_label_set - gt_label_set)
        raise ValueError(
            f"Label set mismatch: missing_in_pred={missing_in_pred} extra_in_pred={extra_in_pred}"
        )

    overall = compute_metrics_from_rows(gt_rows, pred_rows)
    times = [r.get("run_at_raw") for r in pred_rows if r.get("run_at_raw")]
    run_at_raw = max(times) if times else None
    result = {
        "groundtruth_project": groundtruth_project,
        "groundtruth_project_id": gt_id,
        "comparison_project": comparison_project,
        "comparison_project_id": cmp_id,
        "run_at_raw": run_at_raw,
        "metrics": overall,
        "answer_comparison": [],
    }

    result["evaluation_output_path"] = _write_eval_result(result, gt_id, cmp_id)

    # --- Evaluation-over-time logger (SAFE, comparable series only) ---
    # Only log the standard groundtruth set to avoid incomparable datasets.
    if groundtruth_project == SPECIAL_PROJECT_TITLE:
        qal_hash = _qal_hash_from_file()
        model, prompt_hash = _extract_consistent_meta(pred_rows)
        if qal_hash and model and prompt_hash:
            schema_hash = _sha256_text(f"{qal_hash}:{prompt_hash}")
            log_evaluation_over_time(
                {
                    "series": SPECIAL_PROJECT_TITLE,
                    "run_at_raw": run_at_raw,
                    "groundtruth_project_id": int(gt_id),
                    "comparison_project_id": int(cmp_id),
                    "model": model,
                    "qal_hash": qal_hash,
                    "prompt_hash": prompt_hash,
                    "schema_hash": schema_hash,
                    "metrics": overall,
                }
            )
        else:
            # fail-safe: keep log clean (no apples/oranges series)
            safe_logger.info("eval_over_time_skipped_missing_or_inconsistent_meta")

    return result


def get_groundtruth_qal():
    """
    Return the questions_and_labels.json content for the groundtruth project.
    """
    with open(GROUNDTRUTH_QAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
