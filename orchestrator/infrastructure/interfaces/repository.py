# orchestrator/infrastructure/interfaces/repository.py
from abc import ABC, abstractmethod
from typing import List, Optional


class ConversionRepositoryInterface(ABC):
    @abstractmethod
    def project_exists(self, name: str) -> bool: ...

    @abstractmethod
    def create_project(self, name: str) -> None: ...

    @abstractmethod
    def create_file(self, project: str, filename: str, pdf_key: str) -> None: ...

    @abstractmethod
    def create_conversion_job(self, project: str, total_files: int) -> int: ...

    @abstractmethod
    def get_conversion_job(self, job_id: int): ...

    @abstractmethod
    def get_pdf_keys_for_project(self, project: str) -> List[str]: ...

    @abstractmethod
    def set_conversion_job_status(
        self, job_id: int, status: str, error: Optional[str] = None
    ) -> None: ...

    @abstractmethod
    def set_file_html_key(self, project: str, filename: str, html_key: str) -> None: ...

    @abstractmethod
    def increment_converted_files(self, job_id: int) -> None: ...

    @abstractmethod
    def count_files_without_html_key(self, project: str) -> int: ...


class ProjectRepositoryInterface(ABC):
    @abstractmethod
    def project_exists(self, name: str) -> bool: ...

    @abstractmethod
    def set_label_studio_id(self, name: str, label_studio_id: int) -> None: ...

    @abstractmethod
    def get_label_studio_id(self, name: str) -> int | None: ...

    @abstractmethod
    def get_projects_ready_for_upload(self) -> list: ...

    @abstractmethod
    def get_html_keys_for_project(self, name: str) -> list[str]: ...

    @abstractmethod
    def set_ls_tasks_uploaded(self, name: str) -> None: ...
