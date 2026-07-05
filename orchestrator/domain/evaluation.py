# orchestrator/domain/evaluation.py

from collections import defaultdict

from domain.errors import AlreadyExists, InvalidState, NotFound
from domain.models.evaluation import EvaluateProjectsCommand, SaveAsGtSetCommand

from .utils.calculate_metrics import compute_metrics_from_rows
from .utils.shared.label_studio_client import (
    fetch_task_annotations,
    fetch_tasks_page,
    list_projects,
    resolve_project_id,
)


def list_project_names(token: str) -> dict:
    projects = list_projects(token)
    return {"names": [p.get("title") for p in projects if p.get("title")]}


def _bucket_from_results(results: list) -> dict:
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


def _tasks_to_rows(token: str, project_id: int, mode: str) -> list[dict]:
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


def evaluate_projects(cmd: EvaluateProjectsCommand, project_repo, run_repo) -> dict:
    groundtruth_project = cmd.groundtruth_project
    comparison_project = cmd.comparison_project

    if not project_repo.is_groundtruth(groundtruth_project):
        raise InvalidState(
            code="NOT_A_GROUNDTRUTH_SET",
            message=f"Project '{groundtruth_project}' is not a groundtruth set.",
        )

    run = run_repo.get_latest_run(comparison_project)
    if not run:
        raise NotFound(
            code="RUN_NOT_FOUND",
            message=f"No prelabelling run found for project '{comparison_project}'.",
        )

    gt_project_record = project_repo.get_project(groundtruth_project)
    if not gt_project_record:
        raise NotFound(
            code="GROUNDTRUTH_PROJECT_NOT_FOUND",
            message=f"Groundtruth project '{groundtruth_project}' not found.",
        )

    if gt_project_record.labels_hash != run.labels_hash:
        raise InvalidState(
            code="LABEL_MISMATCH",
            message="Groundtruth and comparison project do not share the same label set.",
        )

    gt_html_hashes = project_repo.get_html_hashes_for_project(groundtruth_project)
    cmp_html_hashes = project_repo.get_html_hashes_for_project(comparison_project)

    if gt_html_hashes != cmp_html_hashes:
        raise InvalidState(
            code="HTML_HASH_MISMATCH",
            message="Groundtruth and comparison project do not share identical HTML content.",
            meta={
                "missing_in_comparison": sorted(gt_html_hashes - cmp_html_hashes),
                "extra_in_comparison": sorted(cmp_html_hashes - gt_html_hashes),
            },
        )

    gt_rows = project_repo.get_groundtruth_annotations(groundtruth_project)
    pred_rows = run_repo.build_pred_rows_for_run(run.id)

    overall = compute_metrics_from_rows(gt_rows, pred_rows)
    run_at = run.updated_at if run.updated_at else run.created_at

    run_repo.save_evaluation(
        groundtruth_project=groundtruth_project,
        comparison_prelabelling_run_id=run.id,
        run_at=run_at,
        metrics_micro=overall["micro"],
        metrics_per_label=overall["per_label"],
        filenames_count=overall.get("filenames_count", 0),
    )

    return {
        "groundtruth_project": groundtruth_project,
        "groundtruth_project_id": gt_project_record.id,
        "comparison_project": comparison_project,
        "comparison_project_id": run.id,
        "run_at_raw": run_at.isoformat(),
        "metrics": overall,
        "answer_comparison": [],
        "evaluation_output_path": "",
    }


def get_groundtruth_qals(project_repo) -> dict:
    gt_projects = project_repo.list_groundtruth_projects()
    if not gt_projects:
        raise NotFound(
            code="GROUNDTRUTH_QAL_NOT_FOUND",
            message="No groundtruth sets found.",
        )
    return {"sets": {p.name: p.questions_and_labels for p in gt_projects}}


def get_compatible_groundtruth_sets(comparison_project: str, project_repo, run_repo) -> dict:
    run = run_repo.get_latest_run(comparison_project)
    if not run:
        raise NotFound(
            code="RUN_NOT_FOUND",
            message=f"No prelabelling run found for project '{comparison_project}'.",
        )

    cmp_html_hashes = project_repo.get_html_hashes_for_project(comparison_project)
    if not cmp_html_hashes:
        return {"names": []}

    gt_projects = project_repo.list_groundtruth_projects()
    compatible = []
    for gt in gt_projects:
        if gt.labels_hash != run.labels_hash:
            continue
        gt_html_hashes = project_repo.get_html_hashes_for_project(gt.name)
        if gt_html_hashes == cmp_html_hashes:
            compatible.append(gt.name)

    return {"names": compatible}


def save_as_gt_set(cmd: SaveAsGtSetCommand, project_repo) -> dict:
    source_project = cmd.source_project
    token = cmd.token

    if project_repo.is_groundtruth(source_project):
        raise AlreadyExists(
            code="GT_SET_ALREADY_EXISTS",
            message=f"Project '{source_project}' is already a ground truth set.",
        )

    project_id = resolve_project_id(token, source_project)
    gt_rows = _tasks_to_rows(token, project_id, mode="gt")

    if not gt_rows:
        raise NotFound(
            code="NO_TASKS_FOUND",
            message=f"No tasks found in project '{source_project}'.",
        )

    project_repo.save_groundtruth_annotations(source_project, gt_rows)
    project_repo.set_groundtruth(source_project)

    return {"status": "ok"}
