# orchestrator/infrastructure/repository/prelabelling_run_repository.py

from db.models import PrelabellingRun
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

    def get_run(self, run_id: int):
        return self._db.query(PrelabellingRun).filter(PrelabellingRun.id == run_id).first()

    def set_run_status(self, run_id: int, status: str, error: str | None = None) -> None:
        run = self._db.query(PrelabellingRun).filter(PrelabellingRun.id == run_id).first()
        if run:
            run.status = status
            if error:
                run.error = error
            self._db.flush()
