# orchestrator/domain/models/conversion.py

from typing import List, Optional

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class PrepareConversionCommand(BaseModel):
    project: str
    filenames: List[str]

    @classmethod
    def from_contract(cls, project: str, filenames: List[str]):
        try:
            return cls(project=project, filenames=filenames)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND", message="Invalid command payload.", details=e.errors()
            )


class ConvertCommand(BaseModel):
    job_id: int

    @classmethod
    def from_contract(cls, job_id: int):
        try:
            return cls(job_id=job_id)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND", message="Invalid command payload.", details=e.errors()
            )


class ConversionStatusCommand(BaseModel):
    job_id: int

    @classmethod
    def from_contract(cls, job_id: int):
        try:
            return cls(job_id=job_id)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND", message="Invalid command payload.", details=e.errors()
            )


class ConversionCallbackCommand(BaseModel):
    job_id: int
    filename: str
    html_key: str
    success: bool
    error: Optional[str] = None

    @classmethod
    def from_contract(
        cls, job_id: int, filename: str, html_key: str, success: bool, error: Optional[str] = None
    ):
        try:
            return cls(
                job_id=job_id, filename=filename, html_key=html_key, success=success, error=error
            )
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND", message="Invalid command payload.", details=e.errors()
            )
