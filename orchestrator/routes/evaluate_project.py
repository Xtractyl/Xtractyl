from collections import defaultdict

from routes.utils.calculate_metrics import compute_overall_metrics_from_rows
from routes.utils.evaluate_project_utils import SPECIAL_PROJECT_TITLE, create_evaluation_project
from routes.utils.shared.label_studio_client import (
    fetch_task_annotations,
    fetch_tasks_page,
    list_projects,
    resolve_project_id,
)


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


def _tasks_to_rows(token: str, project_id: int, mode: str) -> list[dict]:
    """
    mode='gt'   -> labels from annotations
    mode='pred' -> labels from predictions
    Returns: [{"filename": str, "task_id": int, "labels": {label: text}}]
    """
    tasks, _total = fetch_tasks_page(token, project_id)
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

        rows.append(
            {
                "task_id": t.get("id"),
                "filename": filename,
                "labels": labels,
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

    overall = compute_overall_metrics_from_rows(gt_rows, pred_rows)

    return {
        "groundtruth_project": groundtruth_project,
        "groundtruth_project_id": gt_id,
        "comparison_project": comparison_project,
        "comparison_project_id": cmp_id,
        "overall_metrics": overall,
        "task_metrics": [],
        "answer_comparison": [],
    }
