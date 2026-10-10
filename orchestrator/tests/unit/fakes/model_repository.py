# orchestrator/tests/unit/fakes/model_repository.py
from infrastructure.interfaces.repository import ModelRepositoryInterface


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
