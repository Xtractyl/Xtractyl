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
    def delete_project_cascade(self, project: str) -> None: ...

    @abstractmethod
    def set_conversion_job_status(
        self, job_id: int, status: str, error: Optional[str] = None
    ) -> None: ...

    @abstractmethod
    def set_file_html_key(
        self,
        project: str,
        filename: str,
        html_key: str,
        pdf_hash: str | None = None,
        html_hash: str | None = None,
    ) -> None: ...

    @abstractmethod
    def set_file_error(self, project: str, filename: str, error: str) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def increment_converted_files(self, job_id: int) -> None: ...


class ProjectRepositoryInterface(ABC):
    @abstractmethod
    def project_exists(self, name: str) -> bool: ...

    @abstractmethod
    def get_project(self, name: str): ...

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

    @abstractmethod
    def save_questions_and_labels(self, name: str, qal: dict) -> None: ...

    @abstractmethod
    def get_questions_and_labels(self, name: str) -> dict | None: ...

    @abstractmethod
    def set_groundtruth(self, name: str) -> None: ...

    @abstractmethod
    def list_groundtruth_projects(self) -> list: ...

    @abstractmethod
    def get_html_hashes_for_project(self, name: str) -> set[str]: ...

    @abstractmethod
    def get_groundtruth_annotations(self, project: str) -> list: ...

    @abstractmethod
    def is_groundtruth(self, name: str) -> bool: ...

    @abstractmethod
    def save_groundtruth_annotations(self, project: str, annotations: list[dict]) -> None: ...


class PrelabellingRunRepositoryInterface(ABC):
    @abstractmethod
    def create_run(
        self,
        project: str,
        label_studio_id: int,
        model: str,
        system_prompt: str,
        questions_and_labels: dict,
    ) -> int: ...

    @abstractmethod
    def get_run(self, job_id: int): ...

    @abstractmethod
    def set_run_status(self, job_id: int, status: str, error: str | None = None) -> None: ...

    @abstractmethod
    def get_latest_run(self, project: str): ...

    @abstractmethod
    def get_task_prelabelling_metas(self, prelabelling_run_id: int) -> list: ...

    @abstractmethod
    def save_task_prelabelling_meta(
        self,
        prelabelling_run_id: int,
        label_studio_task_id: int,
        filename: str,
        predictions: list,
        raw_llm_answers: dict,
        dom_match_diagnostics: list,
        dom_match_by_label: dict,
        task_ms_total: float,
        task_ms_llm_total: float,
        task_ms_dom_extract: float,
        task_ms_dom_match: float,
        n_llm_calls: int,
        n_timeouts: int,
        avg_llm_call_ms: float,
        median_llm_call_ms: float,
    ) -> None: ...

    @abstractmethod
    def save_evaluation(
        self,
        groundtruth_project: str,
        comparison_prelabelling_run_id: int,
        run_at: str,
        metrics_micro: dict,
        metrics_per_label: dict,
        filenames_count: int,
    ) -> int: ...

    @abstractmethod
    def build_pred_rows_for_run(self, prelabelling_run_id: int) -> list: ...

    @abstractmethod
    def get_evaluations_by_groundtruth_project(self, groundtruth_project: str) -> list: ...

    @abstractmethod
    def list_evaluation_series(self) -> list[str]: ...
