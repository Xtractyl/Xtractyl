# orchestrator/domain/evaluation.py

from collections import defaultdict

from sqlalchemy.exc import IntegrityError

from domain.errors import AlreadyExists, InvalidState, NotFound
from domain.models.evaluation import SaveAsGtSetCommand

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


def evaluate_run(run_id: int, groundtruth_project: str, project_repo, run_repo, eval_repo) -> dict:
    """The single place a new evaluation is actually computed and persisted.
    Takes an explicit run_id rather than a project name + "latest run"
    lookup, on purpose: sync_missing_evaluations always knows exactly which
    run and which groundtruth project it means, and using get_latest_run()
    here would reintroduce the ambiguity documented on that method (no
    status filter — could silently resolve to a different, newer or failed
    run than the one intended)."""
    if not project_repo.is_groundtruth(groundtruth_project):
        raise InvalidState(
            code="NOT_A_GROUNDTRUTH_SET",
            message=f"Project '{groundtruth_project}' is not a groundtruth set.",
        )
    run = run_repo.get_run(run_id)
    if not run:
        raise NotFound(
            code="RUN_NOT_FOUND",
            message=f"No prelabelling run found with id '{run_id}'.",
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
    cmp_html_hashes = project_repo.get_html_hashes_for_project(run.project)

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

    eval_repo.save_evaluation(
        groundtruth_project=groundtruth_project,
        comparison_prelabelling_run_id=run.id,
        run_at=run_at,
        metrics_micro=overall["micro"],
        metrics_per_label=overall["per_label"],
        filenames_count=overall.get("filenames_count", 0),
        task_metrics=overall.get("task_metrics"),
        performance=overall.get("performance"),
        labels=overall.get("labels"),
    )

    return {
        "groundtruth_project": groundtruth_project,
        "groundtruth_project_id": gt_project_record.id,
        "comparison_project": run.project,
        "comparison_project_id": run.id,
        "run_at_raw": run_at.isoformat(),
        "metrics": overall,
        "answer_comparison": [],
        "evaluation_output_path": "",
    }


def _serialize_existing_evaluation(existing, project_repo, run_repo, model_repo) -> dict:
    """Formerly a stub. Reshapes an already-persisted Evaluation row into
    the same response shape evaluate_run() returns for a freshly computed
    one, so callers of get_evaluation can't tell the difference.

    Known, accepted gap: only metrics_micro/metrics_per_label/filenames_count
    are persisted on the Evaluation row (see db/models.py) — the richer,
    non-persisted parts of compute_metrics_from_rows()'s output (per-task
    breakdown, performance percentiles, the full label list) are only
    available right after computation, not on replay. If those are needed
    later for the persisted case too, they'd need their own columns rather
    than being reconstructed here — flagging this rather than silently
    returning an incomplete-looking "overall" dict.
    """
    run = run_repo.get_run(existing.comparison_prelabelling_run_id)
    gt_project_record = project_repo.get_project(existing.groundtruth_project)
    model = model_repo.get_by_id(run.model_id) if run else None
    return {
        "groundtruth_project": existing.groundtruth_project,
        "groundtruth_project_id": gt_project_record.id if gt_project_record else None,
        "comparison_project": run.project if run else None,
        "comparison_project_id": existing.comparison_prelabelling_run_id,
        "model": model.archived_name if model else None,
        "run_at_raw": existing.run_at.isoformat() if existing.run_at else None,
        "metrics": {
            "micro": existing.metrics_micro,
            "per_label": existing.metrics_per_label,
            "filenames_count": existing.filenames_count,
            "task_metrics": existing.task_metrics,
            "performance": existing.performance,
            "labels": existing.labels,
        },
        "answer_comparison": [],
        "evaluation_output_path": "",
    }


def get_evaluation(
    groundtruth_project: str, comparison_project: str, project_repo, run_repo, eval_repo, model_repo
) -> dict:
    """Backs the now purely read-only /evaluate-ai endpoint. Deliberately
    does NOT compute on demand: sync_missing_evaluations (called
    automatically from exactly two internal points — a run finishing, a GT
    set being created) is the only place evaluations get created. If this
    raises EVALUATION_NOT_FOUND for a run that is actually 'done' and has a
    matching groundtruth set, that indicates a bug in sync_missing_evaluations
    itself, not a case to silently paper over here — the same reasoning
    that keeps sync_missing_evaluations off any directly callable route in
    the first place: a fallback that computes on demand would let a user
    route around a missing/broken sync just by asking for it."""
    run = run_repo.get_latest_run(comparison_project)
    if not run:
        raise NotFound(
            code="RUN_NOT_FOUND",
            message=f"No prelabelling run found for project '{comparison_project}'.",
        )
    existing = eval_repo.find_evaluation(groundtruth_project, run.id)
    if not existing:
        raise NotFound(
            code="EVALUATION_NOT_FOUND",
            message=(
                f"No evaluation found for run '{run.id}' against groundtruth "
                f"'{groundtruth_project}'. If the run is 'done' and a matching "
                f"groundtruth set exists, this indicates sync_missing_evaluations "
                f"did not run or failed — not something to compute here on demand."
            ),
        )
    return _serialize_existing_evaluation(existing, project_repo, run_repo, model_repo)


def sync_missing_evaluations(project_repo, run_repo, eval_repo) -> None:
    """The single place that creates missing evaluations — called from
    exactly two internal points: handle_prelabel_callback (a run just
    finished) and save_as_gt_set (a new groundtruth set was just created).
    Deliberately NOT exposed as its own route: if a user could trigger this
    selectively, they could also choose not to, and avoid an unwelcome
    evaluation result ever surfacing.

    Scans every (done run) x (groundtruth project) combination with a
    matching (labels_hash, document_set_hash) pair and creates whichever
    Evaluation rows don't exist yet. Both document_set_hash values are read
    directly off Project — set for every project at the end of its
    ConversionJob (see domain/conversion.py), not just groundtruth ones.

    Note on matching fields: only labels_hash + document_set_hash decide
    whether a run is eligible for a given groundtruth set — questions_hash,
    system_prompt and the model used play no role here."""
    gt_projects = [gt for gt in project_repo.list_groundtruth_projects() if gt.document_set_hash]
    gt_by_key: dict[tuple[str, str], list] = {}
    for gt in gt_projects:
        gt_by_key.setdefault((gt.labels_hash, gt.document_set_hash), []).append(gt)

    for run in run_repo.list_done_runs():
        run_project = project_repo.get_project(run.project)
        if not run_project or not run_project.document_set_hash:
            continue
        key = (run.labels_hash, run_project.document_set_hash)
        for gt in gt_by_key.get(key, []):
            if eval_repo.find_evaluation(gt.name, run.id):
                continue
            evaluate_run(run.id, gt.name, project_repo, run_repo, eval_repo)


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


def save_as_gt_set(cmd: SaveAsGtSetCommand, project_repo, run_repo, eval_repo) -> dict:
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

    project = project_repo.get_project(source_project)
    if not project or not project.document_set_hash:
        raise InvalidState(
            code="PROJECT_NOT_CONVERTED",
            message=(
                f"Project '{source_project}' has no document_set_hash yet — "
                f"conversion must complete before it can become a groundtruth set."
            ),
        )

    try:
        project_repo.set_groundtruth(source_project)
    except IntegrityError as e:
        raise AlreadyExists(
            code="GT_SET_CONTENT_ALREADY_EXISTS",
            message=(
                f"Another groundtruth set with the same labels and document "
                f"set already exists; '{source_project}' would be a duplicate."
            ),
        ) from e

    sync_missing_evaluations(project_repo, run_repo, eval_repo)

    return {"status": "ok"}


def resolve_family_for_project(project_name: str, project_repo, run_repo, eval_repo):
    """Given ANY project name the user might pick, resolve the underlying
    (groundtruth_project, run) pair it belongs to. Shared by Comparison
    (here) and Regression/Drift (evaluation_views.py)."""
    project = project_repo.get_project(project_name)
    if not project:
        return None, None

    run = run_repo.get_latest_run(project_name)

    if project.is_groundtruth:
        return project_name, run

    if not run:
        return None, None
    evaluation = eval_repo.find_evaluation_for_run(run.id)
    if not evaluation:
        return None, None
    return evaluation.groundtruth_project, run


def list_evaluated_projects(project_repo, run_repo, eval_repo) -> list[str]:
    """Backs GET /evaluations/projects: every project name that has at
    least one resolvable evaluation family."""
    return eval_repo.list_projects_with_evaluations()


def _entry_to_dict(evaluation, model_name: str | None, run_project: str | None) -> dict:
    return {
        "groundtruth_project": evaluation.groundtruth_project,
        "comparison_prelabelling_run_id": evaluation.comparison_prelabelling_run_id,
        "comparison_project": run_project,
        "model": model_name,
        "run_at_raw": evaluation.run_at.isoformat() if evaluation.run_at else None,
        "metrics": {
            "micro": evaluation.metrics_micro,
            "per_label": evaluation.metrics_per_label,
            "filenames_count": evaluation.filenames_count,
        },
    }


def get_comparison_view(project_name: str, project_repo, run_repo, model_repo, eval_repo) -> dict:
    """Same documents, same labels, model/prompt/questions may vary — a
    ranking of configurations against one fixed groundtruth set. Accepts
    ANY project name (resolved via resolve_family_for_project)."""
    groundtruth_project, _run = resolve_family_for_project(
        project_name, project_repo, run_repo, eval_repo
    )
    if not groundtruth_project:
        return {"entries": []}

    evaluations = eval_repo.get_evaluations_by_groundtruth_project(groundtruth_project)
    entries = []
    for e in evaluations:
        run = run_repo.get_run(e.comparison_prelabelling_run_id)
        model = model_repo.get_by_id(run.model_id) if run else None
        entries.append(
            _entry_to_dict(e, model.archived_name if model else None, run.project if run else None)
        )
    return {"entries": entries}
