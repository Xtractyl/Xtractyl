# orchestrator/domain/models/projects.py

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class CreateProjectCommand(BaseModel):
    token: str
    title: str
    questions: list[str]
    labels: list[str]

    @classmethod
    def from_contract(cls, title: str, questions: list, labels: list, token: str):
        try:
            return cls(token=token, title=title, questions=questions, labels=labels)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class ListQalJsonsCommand(BaseModel):
    project: str

    @classmethod
    def from_contract(cls, project: str):
        try:
            return cls(project=project)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class PreviewQalCommand(BaseModel):
    project: str
    filename: str

    @classmethod
    def from_contract(cls, project: str, filename: str):
        try:
            return cls(project=project, filename=filename)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class ProjectExistsCommand(BaseModel):
    project: str

    @classmethod
    def from_contract(cls, project: str):
        try:
            return cls(project=project)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class UploadTasksCommand(BaseModel):
    project: str
    html_folder: str
    token: str

    @classmethod
    def from_contract(cls, project: str, html_folder: str, token: str):
        try:
            return cls(project=project, html_folder=html_folder, token=token)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )
