# orchestrator/domain/models/jobs.py

from pydantic import BaseModel, ValidationError

from domain.errors import ValidationFailed


class JobStatusCommand(BaseModel):
    job_id: str

    @classmethod
    def from_contract(cls, job_id: str):
        try:
            return cls(job_id=job_id)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class EnqueueJobCommand(BaseModel):
    project_name: str
    model: str
    system_prompt: str
    token: str

    @classmethod
    def from_contract(cls, contract, token: str):
        try:
            return cls(
                project_name=contract.project_name,
                model=contract.model,
                system_prompt=contract.system_prompt,
                token=token,
            )
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class CancelJobCommand(BaseModel):
    job_id: str

    @classmethod
    def from_contract(cls, job_id: str):
        try:
            return cls(job_id=job_id)
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class JobFailedCommand(BaseModel):
    job_id: int
    error: str | None = None

    @classmethod
    def from_contract(cls, contract):
        try:
            return cls(
                job_id=contract.job_id,
                error=contract.error,
            )
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class TaskResultCommand(BaseModel):
    job_id: int
    task_id: int
    filename: str
    success: bool
    error: str | None = None
    result: dict | None = None

    @classmethod
    def from_contract(cls, contract):
        try:
            return cls(
                job_id=contract.job_id,
                task_id=contract.task_id,
                filename=contract.filename,
                success=contract.success,
                error=contract.error,
                result=contract.result.model_dump() if contract.result else None,
            )
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )
