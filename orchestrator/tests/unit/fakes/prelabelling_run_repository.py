# orchestrator/tests/unit/fakes/prelabelling_run_repository.py
from infrastructure.interfaces.repository import PrelabellingRunRepositoryInterface
from sqlalchemy.exc import IntegrityError


class FakePrelabellingRunRepo(PrelabellingRunRepositoryInterface):
    def __init__(
        self,
        existing_run=None,
        new_run_id=1,
        pending_filenames=(),
        resume_succeeds=True,
        create_raises_integrity_error=False,
    ):
        self._existing_run = existing_run
        self._new_run_id = new_run_id
        self._pending_filenames = list(pending_filenames)
        self._resume_succeeds = resume_succeeds
        self._create_raises_integrity_error = create_raises_integrity_error
        self.created_runs = []
        self.created_tasks = []
        self.resumed = []

    def get_run_for_project(self, project):
        return self._existing_run

    def create_run(self, project, model_id, system_prompt):
        if self._create_raises_integrity_error:
            raise IntegrityError("INSERT", {}, Exception("duplicate project"))
        self.created_runs.append((project, model_id, system_prompt))
        return self._new_run_id

    def create_run_tasks(self, run_id, filenames):
        self.created_tasks.append((run_id, list(filenames)))

    def resume_run(self, job_id):
        self.resumed.append(job_id)
        return self._resume_succeeds

    def get_pending_filenames(self, run_id):
        return list(self._pending_filenames)

    def get_run(self, job_id):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def fail_run(self, job_id, error):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def save_run_task_result(
        self, prelabelling_run_id, filename, label_studio_task_id, status, error, result
    ):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def derive_run_status(self, job_id):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def request_cancel(self, job_id):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def apply_cancel(self, job_id):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def get_run_status(self, job_id):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def count_run_tasks(self, run_id):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def get_successful_run_tasks(self, prelabelling_run_id):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def list_done_runs(self):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")

    def get_projects_ready_for_results(self):
        raise NotImplementedError("not needed by prelabel enqueue tests yet")
