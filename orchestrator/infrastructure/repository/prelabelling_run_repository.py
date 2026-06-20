# orchestrator/infrastructure/repository/prelabelling_run_repository.py

from db.models import PrelabellingRun, TaskPrelabellingMeta
from infrastructure.interfaces.repository import PrelabellingRunRepositoryInterface


class PrelabellingRunRepository(PrelabellingRunRepositoryInterface):
    def __init__(self, db):
        self._db = db

    def create_run(
        self,
        project: str,
        label_studio_id: int,
        model: str,
        system_prompt: str,
        questions_and_labels: dict,
    ) -> int:
        run = PrelabellingRun(
            project=project,
            label_studio_id=label_studio_id,
            ollama_model=model,
            system_prompt=system_prompt,
            questions_and_labels=questions_and_labels,
            status="pending",
        )
        self._db.add(run)
        self._db.flush()
        self._db.refresh(run)
        return run.id

    def get_run(self, job_id: int):
        return self._db.query(PrelabellingRun).filter(PrelabellingRun.id == job_id).first()

    def set_run_status(self, job_id: int, status: str, error: str | None = None) -> None:
        run = self._db.query(PrelabellingRun).filter(PrelabellingRun.id == job_id).first()
        if run:
            run.status = status
            if error:
                run.error = error
            self._db.flush()

    def get_latest_run(self, project: str):
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
