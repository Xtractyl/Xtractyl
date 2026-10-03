# orchestrator/domain/results.py
from typing import Any, Dict, List

from domain.errors import InvalidState, NotFound
from domain.models.results import GetResultsTableCommand


def list_projects_ready_for_results(run_repo) -> dict:
    """Backs GET /list_projects_ready_for_results. Restricted to projects
    with a prelabelling_runs row at status="done" """
    return {"projects": run_repo.get_projects_ready_for_results()}


def build_results_table(cmd: GetResultsTableCommand, run_repo):
    run = run_repo.get_run_for_project(cmd.project_name)
    if not run:
        raise NotFound(
            code="RUN_NOT_FOUND",
            message=f"No prelabelling run found for project '{cmd.project_name}'.",
        )
    if run.status != "done":
        raise InvalidState(
            code="RUN_NOT_DONE",
            message=(
                f"Prelabelling run for project '{cmd.project_name}' is not finished "
                f"(status='{run.status}') — results are only available once the run "
                f"has completed successfully."
            ),
        )
    tasks = run_repo.get_successful_run_tasks(run.id)
    if not tasks:
        return {
            "columns": ["task_id", "filename"],
            "rows": [],
            "total": 0,
        }

    label_columns: List[str] = []
    for t in tasks:
        for label in (t.raw_llm_answers or {}).keys():
            col = f"{label}__pred"
            if col not in label_columns:
                label_columns.append(col)

    columns = ["task_id", "filename"] + label_columns
    rows: List[Dict[str, Any]] = []
    for t in tasks:
        flat: Dict[str, Any] = {
            "task_id": t.label_studio_task_id,
            "filename": t.filename,
        }
        for label, val in (t.raw_llm_answers or {}).items():
            flat[f"{label}__pred"] = val.get("answer", "") if isinstance(val, dict) else ""
        rows.append(flat)

    return {
        "columns": columns,
        "rows": rows,
        "total": len(rows),
    }
