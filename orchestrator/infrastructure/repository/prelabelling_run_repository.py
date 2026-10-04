# orchestrator/infrastructure/repository/prelabelling_run_repository.py

from db.models import PrelabellingRun, PrelabellingRunTask
from infrastructure.interfaces.repository import PrelabellingRunRepositoryInterface
from sqlalchemy import case, exists, func
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

    def fail_run(self, job_id: int, error: str | None) -> None:
        self._db.query(PrelabellingRun).filter(
            PrelabellingRun.id == job_id,
            PrelabellingRun.status.in_(
                ("pending", "running")
            ),  # avoids failing a run that finished successfully seconds before (with a callback to /prelabel/task-result)
        ).update({"status": "failed", "error": error}, synchronize_session=False)
        self._db.flush()

    def save_run_task_result(
        self,
        prelabelling_run_id: int,
        filename: str,
        label_studio_task_id: int,
        status: str,
        error: str | None,
        result: dict,
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
        for column, value in result.items():
            setattr(row, column, value)
        self._db.flush()
        return True

    def derive_run_status(self, job_id: int) -> None:
        # derives PrelabellingRun status from tasks in PrelabellingRunTask
        # bumps updated_at for it
        #   - any task still pending            -> running
        #   - no task pending, at least 1 failed -> incomplete
        #   - no task pending, none failed       -> running (the end-of-job callback sets done)
        open_tasks = (
            exists()
            .where(
                PrelabellingRunTask.prelabelling_run_id == PrelabellingRun.id,
                PrelabellingRunTask.status == "pending",
            )
            .correlate(PrelabellingRun)
        )
        failed_tasks = (
            exists()
            .where(
                PrelabellingRunTask.prelabelling_run_id == PrelabellingRun.id,
                PrelabellingRunTask.status == "failed",
            )
            .correlate(PrelabellingRun)
        )
        # Order is of importance, CASE takes the first matching branch, so
        # given open tasks a run with a failed task
        # gets status "running" even though a failed task already exists, which is what we want
        new_status = case(
            (open_tasks, "running"),
            (failed_tasks, "incomplete"),
            else_="done",
        )
        self._db.query(PrelabellingRun).filter(
            PrelabellingRun.id == job_id,
            PrelabellingRun.status.in_(("pending", "running")),
        ).update({"status": new_status, "updated_at": func.now()}, synchronize_session=False)
        self._db.flush()

    def request_cancel(self, job_id: int) -> bool:
        updated = (
            self._db.query(PrelabellingRun)
            .filter(
                PrelabellingRun.id == job_id,
                PrelabellingRun.status.in_(("pending", "running")),
            )
            .update({"cancel_requested": True}, synchronize_session=False)
        )
        self._db.flush()
        return updated == 1

    def apply_cancel(self, job_id: int) -> bool:
        # called right after derive_run_status (jobs that are determined to be finished don't need
        # cancelling anymore
        updated = (
            self._db.query(PrelabellingRun)
            .filter(
                PrelabellingRun.id == job_id,
                PrelabellingRun.status == "running",
                PrelabellingRun.cancel_requested.is_(True),
            )
            .update({"status": "cancelled"}, synchronize_session=False)
        )
        self._db.flush()
        return updated == 1

    def get_run_status(self, job_id: int) -> str | None:
        return self._db.query(PrelabellingRun.status).filter(PrelabellingRun.id == job_id).scalar()

    def count_run_tasks(self, run_id: int) -> tuple[int, int]:
        """(total tasks, tasks that are no longer pending) of a run."""
        total, finished = (
            self._db.query(
                func.count(PrelabellingRunTask.id),
                func.count(case((PrelabellingRunTask.status != "pending", 1))),
            )
            .filter(PrelabellingRunTask.prelabelling_run_id == run_id)
            .one()
        )
        return total, finished

    def resume_run(self, job_id: int) -> bool:
        updated = (
            self._db.query(PrelabellingRun)
            .filter(
                PrelabellingRun.id == job_id,
                PrelabellingRun.status.in_(("failed", "cancelled", "incomplete")),
            )
            .update({"status": "pending", "error": None}, synchronize_session=False)
        )
        if updated == 1:
            self._db.query(PrelabellingRunTask).filter(
                PrelabellingRunTask.prelabelling_run_id == job_id,
                PrelabellingRunTask.status == "failed",
            ).update({"status": "pending", "error": None}, synchronize_session=False)
        self._db.flush()
        return updated == 1

    def get_run_for_project(self, project: str):
        return (
            self._db.query(PrelabellingRun)
            .filter(PrelabellingRun.project == project)
            .order_by(PrelabellingRun.created_at.desc())
            .first()
        )

    def get_successful_run_tasks(self, prelabelling_run_id: int) -> list:
        return (
            self._db.query(PrelabellingRunTask)
            .filter(
                PrelabellingRunTask.prelabelling_run_id == prelabelling_run_id,
                PrelabellingRunTask.status == "success",
            )
            .order_by(PrelabellingRunTask.id)
            .all()
        )

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
