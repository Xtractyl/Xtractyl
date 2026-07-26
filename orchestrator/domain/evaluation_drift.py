# orchestrator/domain/evaluation_drift.py


from domain.models.evaluation_drift import GetEvaluationDriftCommand


def get_evaluation_drift(
    cmd: GetEvaluationDriftCommand, run_repo, project_repo, model_repo
) -> dict:
    gt_projects = project_repo.list_groundtruth_projects()
    known_series = sorted([p.name for p in gt_projects])

    sets = []
    for series in known_series:
        evaluations = run_repo.get_evaluations_by_groundtruth_project(series)
        entries = []
        for e in evaluations:
            run = run_repo.get_run(e.comparison_prelabelling_run_id)
            qal = (run.questions_and_labels or {}) if run else {}
            model = model_repo.get_by_id(run.model_id) if run else None

            entries.append(
                {
                    "series": series,
                    "run_at_raw": e.run_at.isoformat() if e.run_at else None,
                    "groundtruth_project_id": e.id,
                    "comparison_project_id": e.comparison_prelabelling_run_id,
                    "model": model.archived_name if model else "",
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
