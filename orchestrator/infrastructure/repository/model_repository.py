# orchestrator/infrastructure/repository/model_repository.py
from db.models import Model
from infrastructure.interfaces.repository import ModelRepositoryInterface
from sqlalchemy import func


class ModelRepository(ModelRepositoryInterface):
    def __init__(self, db):
        self._db = db

    def get_by_digest(self, digest: str):
        return self._db.query(Model).filter(Model.digest == digest).first()

    def get_by_id(self, model_id: int):
        return self._db.query(Model).filter(Model.id == model_id).first()

    def get_by_archived_name(self, archived_name: str):
        return self._db.query(Model).filter(Model.archived_name == archived_name).first()

    def touch(self, model_id: int) -> None:
        model = self.get_by_id(model_id)
        if model:
            model.last_confirmed_at = func.now()
            self._db.flush()

    def create(
        self,
        tag: str,
        digest: str,
        archived_name: str,
        size_bytes: int | None,
        family: str | None,
        parameter_size: str | None,
        quantization_level: str | None,
        ollama_version: str | None,
        pulled_via: str,
    ) -> int:
        model = Model(
            tag=tag,
            digest=digest,
            archived_name=archived_name,
            size_bytes=size_bytes,
            family=family,
            parameter_size=parameter_size,
            quantization_level=quantization_level,
            ollama_version=ollama_version,
            pulled_via=pulled_via,
            status="downloaded",
        )
        self._db.add(model)
        self._db.flush()
        self._db.refresh(model)
        return model.id
