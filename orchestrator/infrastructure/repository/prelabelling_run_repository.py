# orchestrator/infrastructure/repository/prelabelling_run_repository.py

from db.models import PrelabellingRun, PrelabellingRunTask, TaskPrelabellingMeta
from infrastructure.interfaces.repository import PrelabellingRunRepositoryInterface
from utils.hashing import compute_system_prompt_hash


class PrelabellingRunRepository(PrelabellingRunRepositoryInterface):
    def __init__(self, db):
        self._db = db

    def create_run(
        self,
        project: str,
        model_id: int,
        system_prompt: str,
    ) -> int:
        run = PrelabellingRun(
            project=project,
            model_id=model_id,
            system_prompt=system_prompt or "",
            system_prompt_hash=compute_system_prompt_hash(system_prompt),
            status="pending",
        )
        self._db.add(run)
        self._db.flush()
        self._db.refresh(run)
        return run.id

    def create_run_tasks(self, run_id: int, filenames: list[str]) -> None:
        self._db.add_all(
            PrelabellingRunTask(prelabelling_run_id=run_id, filename=name, status="pending")
            for name in filenames
        )
        self._db.flush()

    def get_run(self, job_id: int):
        return self._db.query(PrelabellingRun).filter(PrelabellingRun.id == job_id).first()

    def set_run_status(self, job_id: int, status: str, error: str | None = None) -> None:
        run = self._db.query(PrelabellingRun).filter(PrelabellingRun.id == job_id).first()
        if run:
            run.status = status
            if error:
                run.error = error
            self._db.flush()

    def save_run_task_result(
        self,
        prelabelling_run_id: int,
        filename: str,
        label_studio_task_id: int,
        status: str,
        error: str | None,
        predictions: list | None,
        raw_llm_answers: dict | None,
        dom_match_diagnostics: list | None,
        dom_match_by_label: dict | None,
        task_ms_total: float | None,
        task_ms_llm_total: float | None,
        task_ms_dom_extract: float | None,
        task_ms_dom_match: float | None,
        n_llm_calls: int | None,
        n_timeouts: int | None,
        avg_llm_call_ms: float | None,
        median_llm_call_ms: float | None,
    ) -> bool:
        row = (
            self._db.query(PrelabellingRunTask)
            .filter(
                PrelabellingRunTask.prelabelling_run_id == prelabelling_run_id,
                PrelabellingRunTask.filename == filename,
            )
            .first()
        )
        if row is None:
            return False
        row.label_studio_task_id = label_studio_task_id
        row.status = status
        row.error = error
        row.predictions = predictions
        row.raw_llm_answers = raw_llm_answers
        row.dom_match_diagnostics = dom_match_diagnostics
        row.dom_match_by_label = dom_match_by_label
        row.task_ms_total = task_ms_total
        row.task_ms_llm_total = task_ms_llm_total
        row.task_ms_dom_extract = task_ms_dom_extract
        row.task_ms_dom_match = task_ms_dom_match
        row.n_llm_calls = n_llm_calls
        row.n_timeouts = n_timeouts
        row.avg_llm_call_ms = avg_llm_call_ms
        row.median_llm_call_ms = median_llm_call_ms
        self._db.flush()
        return True

    def resume_run(self, job_id: int) -> bool:
        updated = (
            self._db.query(PrelabellingRun)
            .filter(
                PrelabellingRun.id == job_id,
                PrelabellingRun.status.in_(("failed", "cancelled", "incomplete")),
            )
            .update({"status": "pending", "error": None}, synchronize_session=False)
        )
        self._db.flush()
        return updated == 1

    def get_run_for_project(self, project: str):
        return (
            self._db.query(PrelabellingRun)
            .filter(PrelabellingRun.project == project)
            .order_by(PrelabellingRun.created_at.desc())
            .first()
        )

    def get_task_prelabelling_metas(self, prelabelling_run_id: int) -> list:
        return (
            self._db.query(TaskPrelabellingMeta)
            .filter(TaskPrelabellingMeta.prelabelling_run_id == prelabelling_run_id)
            .all()
        )

    def save_task_prelabelling_meta(
        self,
        prelabelling_run_id: int,
        label_studio_task_id: int,
        filename: str,
        predictions: list,
        raw_llm_answers: dict,
        dom_match_diagnostics: list,
        dom_match_by_label: dict,
        task_ms_total: float,
        task_ms_llm_total: float,
        task_ms_dom_extract: float,
        task_ms_dom_match: float,
        n_llm_calls: int,
        n_timeouts: int,
        avg_llm_call_ms: float,
        median_llm_call_ms: float,
    ) -> None:
        meta = TaskPrelabellingMeta(
            prelabelling_run_id=prelabelling_run_id,
            label_studio_task_id=label_studio_task_id,
            filename=filename,
            predictions=predictions,
            raw_llm_answers=raw_llm_answers,
            dom_match_diagnostics=dom_match_diagnostics,
            dom_match_by_label=dom_match_by_label,
            task_ms_total=task_ms_total,
            task_ms_llm_total=task_ms_llm_total,
            task_ms_dom_extract=task_ms_dom_extract,
            task_ms_dom_match=task_ms_dom_match,
            n_llm_calls=n_llm_calls,
            n_timeouts=n_timeouts,
            avg_llm_call_ms=avg_llm_call_ms,
            median_llm_call_ms=median_llm_call_ms,
        )
        self._db.add(meta)
        self._db.flush()

    def build_pred_rows_for_run(self, prelabelling_run_id: int) -> list:
        metas = self.get_task_prelabelling_metas(prelabelling_run_id)
        rows = []
        for m in metas:
            labels = {
                label: (val.get("answer", "") if isinstance(val, dict) else "")
                for label, val in (m.raw_llm_answers or {}).items()
            }
            rows.append(
                {
                    "filename": m.filename,
                    "labels": labels,
                    "meta": {
                        "raw_llm_answers": m.raw_llm_answers,
                        "performance": {
                            "request": {
                                "task_ms_total": m.task_ms_total,
                                "task_ms_llm_total": m.task_ms_llm_total,
                                "task_ms_dom_extract": m.task_ms_dom_extract,
                                "task_ms_dom_match": m.task_ms_dom_match,
                            }
                        },
                    },
                }
            )
        return rows

    def list_done_runs(self) -> list:
        return self._db.query(PrelabellingRun).filter(PrelabellingRun.status == "done").all()

    def get_projects_ready_for_results(self) -> list[str]:
        rows = (
            self._db.query(PrelabellingRun.project)
            .filter(PrelabellingRun.status == "done")
            .order_by(PrelabellingRun.project.asc())
            .all()
        )
        return [r[0] for r in rows]
