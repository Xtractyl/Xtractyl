# orchestrator/domain/evaluation.py

import json
import os
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from utils.logging_utils import log_evaluation_over_time, safe_logger

from domain.errors import AlreadyExists, ExternalServiceError, InvalidState, NotFound
from domain.models.evaluation import EvaluateProjectsCommand, SaveAsGtSetCommand

from .utils.calculate_metrics import compute_metrics_from_rows
from .utils.evaluate_project_utils import LABEL_STUDIO_URL, _auth_headers, create_evaluation_project
from .utils.shared.label_studio_client import (
    fetch_task_annotations,
    fetch_tasks_page,
    list_projects,
    resolve_project_id,
)

GROUNDTRUTH_QAL_DIR = Path(
    os.getenv(
        "GROUNDTRUTH_QAL_DIR",
        "/app/data/projects/Evaluation_Sets_Do_Not_Delete",
    )
)


EVAL_OUT_DIR = Path(os.getenv("EVAL_DIR", "/app/data/evaluation"))


def _list_gt_sets() -> list[dict]:
    """
    Returns all GT sets found in GROUNDTRUTH_QAL_DIR.
    Each entry: {"name": str, "qal": dict}
    """
    sets = []
    if not GROUNDTRUTH_QAL_DIR.is_dir():
        return sets
    for subfolder in sorted(GROUNDTRUTH_QAL_DIR.iterdir()):
        if not subfolder.is_dir():
            continue
        qal_path = subfolder / "questions_and_labels.json"
        if not qal_path.is_file():
            continue
        try:
            with open(qal_path, "r", encoding="utf-8") as f:
                qal = json.load(f)
            sets.append({"name": subfolder.name, "qal": qal})
        except Exception:
            continue
    return sets


def _extract_consistent_model(pred_rows: list[dict]) -> str | None:
    """Returns the model name if consistent across all tasks, else None."""
    models = {
        r.get("meta", {}).get("model") for r in pred_rows or [] if isinstance(r.get("meta"), dict)
    }
    models.discard(None)
    return next(iter(models)) if len(models) == 1 else None


def list_project_names(token: str) -> dict:
    """
    List all project titles available in Label Studio.

    Args:
        token: Label Studio API token.

    Returns:
        {"names": list[str]}
    """
    projects = list_projects(token)
    return {"names": [p.get("title") for p in projects if p.get("title")]}


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
    """
    Compare a comparison project against a groundtruth project and compute evaluation metrics.
    If the groundtruth project is a known GT set and does not exist in Label Studio yet,
    it will be created automatically. Results are written to the evaluation output directory.
    For any known GT set, metrics are also appended to the evaluation-over-time log.

    Args:
        cmd: EvaluateProjectsCommand with token, groundtruth_project, and comparison_project.

    Returns:
        EvaluateProjectsResponse-compatible dict with metrics, answer_comparison,
        project ids, run_at_raw, and evaluation_output_path.

    Raises:
        NotFound: If groundtruth or comparison project does not exist in Label Studio.
        InvalidState: If filenames or label sets between projects do not match.
    """

    token = cmd.token
    groundtruth_project = cmd.groundtruth_project
    comparison_project = cmd.comparison_project
    gt_sets_by_name = {s["name"]: s["qal"] for s in _list_gt_sets()}

    try:
        gt_id = resolve_project_id(token, groundtruth_project)
    except NotFound:
        if groundtruth_project in gt_sets_by_name:
            gt_id = create_evaluation_project(token, groundtruth_project)

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
        raise InvalidState(
            code="FILENAME_MISMATCH",
            message="Filenames in groundtruth and comparison project do not match.",
            meta={"missing_in_pred": missing_in_pred[:20], "extra_in_pred": extra_in_pred[:20]},
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
        raise InvalidState(
            code="LABEL_MISMATCH",
            message="Label sets in groundtruth and comparison project do not match.",
            meta={"missing_in_pred": missing_in_pred, "extra_in_pred": extra_in_pred},
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

    if groundtruth_project in gt_sets_by_name:
        qal = gt_sets_by_name[groundtruth_project]
        model = _extract_consistent_model(pred_rows)
        system_prompt = next(
            (r.get("meta", {}).get("system_prompt") for r in pred_rows if r.get("meta")),
            None,
        )
        if model and system_prompt:
            questions = None
            qal_labels = qal.get("labels", [])
            raw_answers = next(
                (
                    r.get("meta", {}).get("raw_llm_answers", {})
                    for r in pred_rows
                    if r.get("meta", {}).get("raw_llm_answers")
                ),
                {},
            )
            if raw_answers and qal_labels:
                questions = [
                    raw_answers.get(label, {}).get("question")
                    for label in qal_labels
                    if raw_answers.get(label, {}).get("question")
                ]
            log_evaluation_over_time(
                {
                    "series": groundtruth_project,
                    "run_at_raw": run_at_raw,
                    "groundtruth_project_id": int(gt_id),
                    "comparison_project_id": int(cmp_id),
                    "model": model,
                    "system_prompt": system_prompt,
                    "questions": questions,
                    "labels": qal_labels,
                    "metrics": overall,
                }
            )
        else:
            # fail-safe: keep log clean (no apples/oranges series)
            safe_logger.info("eval_over_time_skipped_missing_or_inconsistent_meta")

    return result


def get_groundtruth_qals() -> list[dict]:
    """
    Load all groundtruth QAL files from GROUNDTRUTH_QAL_DIR subfolders.

    Returns:
        List of {"name": str, "qal": dict}

    Raises:
        NotFound: If the base directory does not exist or contains no valid sets.
    """
    sets = _list_gt_sets()
    if not sets:
        raise NotFound(
            code="GROUNDTRUTH_QAL_NOT_FOUND",
            message="No groundtruth sets found.",
        )
    return sets


def save_as_gt_set(cmd: SaveAsGtSetCommand, token: str) -> dict:
    """
    Save an existing Label Studio project as a ground truth set.
    Exports tasks from Label Studio, copies HTMLs, PDFs and QAL,
    and stores everything under GROUNDTRUTH_QAL_DIR/<gt_set_name>/.

    Args:
        cmd: SaveAsGtSetCommand with source_project and gt_set_name.
        token: Label Studio API token.

    Raises:
        ValidationFailed: If gt_set_name already exists as a GT set.
        NotFound: If source project or required folders do not exist.
        ExternalServiceError: If Label Studio export fails.

    Returns:
        {"gt_set_name": str}
    """
    source_project = cmd.source_project
    gt_set_name = cmd.gt_set_name

    # Check gt_set_name not already taken
    target_dir = GROUNDTRUTH_QAL_DIR / gt_set_name
    if target_dir.exists():
        raise AlreadyExists(
            code="GT_SET_ALREADY_EXISTS",
            message=f"A ground truth set with the name '{gt_set_name}' already exists.",
        )

    # Check QAL exists for source project
    qal_src = Path("data") / "projects" / source_project / "questions_and_labels.json"
    if not qal_src.is_file():
        raise NotFound(
            code="QAL_NOT_FOUND",
            message=f"questions_and_labels.json not found for project '{source_project}'.",
        )

    # Export tasks from Label Studio in GUI export format
    gt_project_id = resolve_project_id(token, source_project)
    try:
        export_resp = requests.get(
            f"{LABEL_STUDIO_URL}/api/projects/{gt_project_id}/export?exportType=JSON",
            headers={**_auth_headers(token), "Content-Type": "application/json"},
            timeout=60,
        )
        export_resp.raise_for_status()
        tasks = export_resp.json()
    except requests.RequestException:
        raise ExternalServiceError(
            code="LABEL_STUDIO_EXPORT_FAILED",
            message=f"Failed to export tasks from project '{source_project}'.",
        )
    if not tasks:
        raise NotFound(
            code="NO_TASKS_FOUND",
            message=f"No tasks found in project '{source_project}'.",
        )

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Save Evaluation_Set.json
    eval_set_path = target_dir / "Evaluation_Set.json"
    eval_set_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

    # Copy QAL
    shutil.copy2(qal_src, target_dir / "questions_and_labels.json")

    # Copy HTMLs
    html_src = Path("data") / "htmls" / source_project
    html_dst = Path("data") / "htmls" / "Evaluation_Sets_Do_Not_Delete" / gt_set_name
    if html_src.is_dir():
        shutil.copytree(html_src, html_dst)

    # Copy PDFs
    pdf_src = Path("data") / "pdfs" / source_project
    pdf_dst = Path("data") / "pdfs" / "Evaluation_Sets_Do_Not_Delete" / gt_set_name
    if pdf_src.is_dir():
        shutil.copytree(pdf_src, pdf_dst)

    return {"gt_set_name": gt_set_name}
