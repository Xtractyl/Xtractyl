# orchestrator/infrastructure/repository/project_repository.py

from db.models import File, Project, TaskGroundtruthAnnotation
from infrastructure.interfaces.repository import ProjectRepositoryInterface
from utils.hashing import compute_labels_hash


class ProjectRepository(ProjectRepositoryInterface):
    def __init__(self, db):
        self._db = db

    def project_exists(self, name: str) -> bool:
        return self._db.query(Project).filter(Project.name == name).first() is not None

    def get_project(self, name: str):
        return self._db.query(Project).filter(Project.name == name).first()

    def set_label_studio_id(self, name: str, label_studio_id: int) -> None:
        project = self._db.query(Project).filter(Project.name == name).first()
        if project:
            project.label_studio_id = label_studio_id
            self._db.flush()

    def get_label_studio_id(self, name: str) -> int | None:
        project = self._db.query(Project).filter(Project.name == name).first()
        return project.label_studio_id if project else None

    def get_projects_ready_for_upload(self) -> list:
        return (
            self._db.query(Project)
            .filter(
                Project.label_studio_id.isnot(None),
                Project.ls_tasks_uploaded.is_(False),
            )
            .all()
        )

    def get_projects_without_label_studio_id(self) -> list:
        return self._db.query(Project).filter(Project.label_studio_id.is_(None)).all()

    def get_html_keys_for_project(self, name: str) -> list[str]:
        files = (
            self._db.query(File)
            .filter(
                File.project == name,
                File.html_key.isnot(None),
            )
            .all()
        )
        return [f.html_key for f in files]

    def set_ls_tasks_uploaded(self, name: str) -> None:
        project = self._db.query(Project).filter(Project.name == name).first()
        if project:
            project.ls_tasks_uploaded = True
            self._db.flush()

    def save_questions_and_labels(self, name: str, qal: dict) -> None:
        project = self._db.query(Project).filter(Project.name == name).first()
        if project:
            project.questions_and_labels = qal
            project.labels_hash = compute_labels_hash(qal.get("labels", []))
            self._db.flush()

    def get_questions_and_labels(self, name: str) -> dict | None:
        project = self._db.query(Project).filter(Project.name == name).first()
        return project.questions_and_labels if project else None

    def is_groundtruth(self, name: str) -> bool:
        project = self._db.query(Project).filter(Project.name == name).first()
        return bool(project and project.is_groundtruth)

    def set_groundtruth(self, name: str) -> None:
        project = self._db.query(Project).filter(Project.name == name).first()
        if project:
            project.is_groundtruth = True
            self._db.flush()

    def save_groundtruth_annotations(self, project: str, annotations: list[dict]) -> None:
        for row in annotations:
            self._db.add(
                TaskGroundtruthAnnotation(
                    project=project,
                    label_studio_task_id=row["task_id"],
                    filename=row["filename"],
                    annotations=row["labels"],
                )
            )
        self._db.flush()

    def list_groundtruth_projects(self) -> list:
        return self._db.query(Project).filter(Project.is_groundtruth.is_(True)).all()

    def get_html_hashes_for_project(self, name: str) -> set[str]:
        files = self._db.query(File).filter(File.project == name).all()
        return {f.html_hash for f in files}

    def get_groundtruth_annotations(self, project: str) -> list:
        rows = (
            self._db.query(TaskGroundtruthAnnotation)
            .filter(TaskGroundtruthAnnotation.project == project)
            .all()
        )
        return [{"filename": r.filename, "labels": r.annotations or {}} for r in rows]
