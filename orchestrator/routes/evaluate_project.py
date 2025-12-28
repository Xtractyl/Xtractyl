import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from routes.utils.calculate_metrics import compute_metrics_from_rows
from routes.utils.evaluate_project_utils import SPECIAL_PROJECT_TITLE, create_evaluation_project
from routes.utils.shared.label_studio_client import (
    fetch_task_annotations,
    fetch_tasks_page,
    list_projects,
    resolve_project_id,
)

EVAL_OUT_DIR = Path(os.getenv("EVAL_DIR", "/app/data/evaluation"))


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

        rows.append(
            {
                "task_id": t.get("id"),
                "filename": filename,
                "labels": labels,
                "meta": meta,
            }
        )

    return rows


def evaluate_projects(token: str, groundtruth_project: str, comparison_project: str) -> dict:
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
    result = {
        "groundtruth_project": groundtruth_project,
        "groundtruth_project_id": gt_id,
        "comparison_project": comparison_project,
        "comparison_project_id": cmp_id,
        "metrics": overall,
        "answer_comparison": [],
    }

    result["evaluation_output_path"] = _write_eval_result(result, gt_id, cmp_id)
    return result
