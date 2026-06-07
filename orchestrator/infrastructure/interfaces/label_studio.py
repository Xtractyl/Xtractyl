# orchestrator/infrastructure/interfaces/label_studio.py

from abc import ABC, abstractmethod


class LabelStudioInterface(ABC):
    @abstractmethod
    def create_project(self, title: str, label_config: str, token: str) -> int: ...

    @abstractmethod
    def attach_ml_backend(self, project_id: int, token: str) -> None: ...

    @abstractmethod
    def upload_tasks(self, project_id: int, tasks: list, token: str) -> None: ...
