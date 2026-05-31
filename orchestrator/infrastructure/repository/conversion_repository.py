# orchestrator/infrastructure/repository/conversion_repository.py
from typing import List, Optional

from db.models import ConversionJob, File, Project
from infrastructure.interfaces.repository import ConversionRepositoryInterface


class ConversionRepository(ConversionRepositoryInterface):
    def __init__(self, db):
        self._db = db

    def project_exists(self, name: str) -> bool:
        return self._db.query(Project).filter(Project.name == name).first() is not None

    def create_project(self, name: str) -> None:
        project = Project(name=name, questions_and_labels={})
        self._db.add(project)
        self._db.flush()

    def create_file(self, project: str, filename: str, pdf_key: str) -> None:
        self._db.add(File(project=project, filename=filename, pdf_key=pdf_key))
        self._db.flush()

    def create_conversion_job(self, project: str, total_files: int) -> int:
        job = ConversionJob(
            project=project,
            status="pending",
            total_files=total_files,
            converted_files=0,
        )
        self._db.add(job)
        self._db.flush()
        self._db.refresh(job)
        return job.id

    def get_conversion_job(self, job_id: int):
        return self._db.query(ConversionJob).filter(ConversionJob.id == job_id).first()

    def get_pdf_keys_for_project(self, project: str) -> List[str]:
        files = self._db.query(File).filter(File.project == project).all()
        return [f.pdf_key for f in files if f.pdf_key]

    def set_conversion_job_status(
        self, job_id: int, status: str, error: Optional[str] = None
    ) -> None:
        job = self.get_conversion_job(job_id)
        if job:
            job.status = status
            if error:
                job.error = error
            self._db.flush()

    def set_file_html_key(self, project: str, filename: str, html_key: str) -> None:
        file_record = (
            self._db.query(File).filter(File.project == project, File.filename == filename).first()
        )
        if file_record:
            file_record.html_key = html_key
            self._db.flush()

    def increment_converted_files(self, job_id: int) -> None:
        job = self.get_conversion_job(job_id)
        if job:
            job.converted_files += 1
            self._db.flush()

    def count_files_without_html_key(self, project: str) -> int:
        return self._db.query(File).filter(File.project == project, File.html_key.is_(None)).count()
