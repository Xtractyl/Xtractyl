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
    questions_and_labels: dict
    token: str

    @classmethod
    def from_contract(cls, contract, token: str):
        try:
            return cls(
                project_name=contract.project_name,
                model=contract.model,
                system_prompt=contract.system_prompt,
                questions_and_labels=contract.questions_and_labels.model_dump(),
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


class PrelabelCallbackCommand(BaseModel):
    job_id: str
    status: str
    error: str | None = None

    @classmethod
    def from_contract(cls, contract):
        try:
            return cls(
                job_id=contract.job_id,
                status=contract.status,
                error=contract.error,
            )
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )


class TaskPrelabellingMetaCommand(BaseModel):
    job_id: int
    task_id: int
    filename: str
    predictions: list
    raw_llm_answers: dict
    dom_match_diagnostics: list
    dom_match_by_label: dict
    task_ms_total: float
    task_ms_llm_total: float
    task_ms_dom_extract: float
    task_ms_dom_match: float
    n_llm_calls: int
    n_timeouts: int
    avg_llm_call_ms: float
    median_llm_call_ms: float

    @classmethod
    def from_contract(cls, contract):
        try:
            return cls(
                job_id=int(contract.job_id),
                task_id=contract.task_id,
                filename=contract.filename,
                predictions=contract.predictions,
                raw_llm_answers=contract.raw_llm_answers,
                dom_match_diagnostics=contract.dom_match_diagnostics,
                dom_match_by_label=contract.dom_match_by_label,
                task_ms_total=contract.task_ms_total,
                task_ms_llm_total=contract.task_ms_llm_total,
                task_ms_dom_extract=contract.task_ms_dom_extract,
                task_ms_dom_match=contract.task_ms_dom_match,
                n_llm_calls=contract.n_llm_calls,
                n_timeouts=contract.n_timeouts,
                avg_llm_call_ms=contract.avg_llm_call_ms,
                median_llm_call_ms=contract.median_llm_call_ms,
            )
        except ValidationError as e:
            raise ValidationFailed(
                code="INVALID_COMMAND",
                message="Invalid command payload.",
                details=e.errors(),
            )
