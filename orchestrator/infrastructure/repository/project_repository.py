# orchestrator/infrastructure/repository/project_repository.py

from db.models import Project
from infrastructure.interfaces.repository import ProjectRepositoryInterface


class ProjectRepository(ProjectRepositoryInterface):
    def __init__(self, db):
        self._db = db

    def project_exists(self, name: str) -> bool:
        return self._db.query(Project).filter(Project.name == name).first() is not None

    def set_label_studio_id(self, name: str, label_studio_id: int) -> None:
        project = self._db.query(Project).filter(Project.name == name).first()
        if project:
            project.label_studio_id = label_studio_id
            self._db.flush()
