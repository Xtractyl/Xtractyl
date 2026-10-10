# orchestrator/tests/unit/fakes/jobs_fakes.py
from db.models import Model, PrelabellingRun
from infrastructure.interfaces.queue import PrelabelQueueInterface
from infrastructure.interfaces.repository import (
    ModelRepositoryInterface,
    PrelabellingRunRepositoryInterface,
)
from sqlalchemy.exc import IntegrityError
from utils.hashing import compute_system_prompt_hash


class FakePrelabelQueue(PrelabelQueueInterface):
    def __init__(self):
        self.pushed = []

    def push_prelabel_job(self, payload):
        self.pushed.append(payload)


def make_model(model_id, archived_name):
    return Model(id=model_id, archived_name=archived_name)


def make_run(status, model_id=1, system_prompt="Extract.", project="proj", run_id=1):
    return PrelabellingRun(
        id=run_id,
        project=project,
        model_id=model_id,
        system_prompt=system_prompt,
        system_prompt_hash=compute_system_prompt_hash(system_prompt),
        status=status,
    )


class FakeModelRepo(ModelRepositoryInterface):
    def __init__(self, models=None):
        self.models = {m.archived_name: m for m in (models or [])}

    def get_by_archived_name(self, archived_name):
        return self.models.get(archived_name)

    def get_by_id(self, model_id):
        return next((m for m in self.models.values() if m.id == model_id), None)

    def get_by_digest(self, digest):
        raise NotImplementedError("not needed by prelabel domain tests yet")

    def list_archived_names(self):
        raise NotImplementedError("not needed by prelabel domain tests yet")

    def touch(self, model_id):
        raise NotImplementedError("not needed by prelabel domain tests yet")

    def commit(self):
        raise NotImplementedError("not needed by prelabel domain tests yet")

    def rollback(self):
        raise NotImplementedError("not needed by prelabel domain tests yet")

    def create(
        self,
        tag,
        digest,
        archived_name,
        size_bytes,
        family,
        parameter_size,
        quantization_level,
        ollama_version,
        pulled_via,
    ):
        raise NotImplementedError("not needed by prelabel domain tests yet")


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
