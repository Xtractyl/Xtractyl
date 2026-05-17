# orchestrator/api/contracts/conversion.py

from typing import List, Optional

from pydantic import BaseModel, field_validator


class PrepareConversionRequest(BaseModel):
    project: str
    filenames: List[str]

    @field_validator("project")
    @classmethod
    def project_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("project name must be at least 3 characters")
        return v.strip()

    @field_validator("filenames")
    @classmethod
    def filenames_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("filenames must not be empty")
        return v


class PresignedUrl(BaseModel):
    filename: str
    upload_url: str
    pdf_key: str


class PrepareConversionResponse(BaseModel):
    job_id: int
    presigned_urls: List[PresignedUrl]


class ConvertRequest(BaseModel):
    job_id: int


class ConvertResponse(BaseModel):
    job_id: int
    status: str


class ConversionStatusResponse(BaseModel):
    job_id: int
    status: str  # pending | converting | done | failed
    total_files: int
    converted_files: int
    error: Optional[str] = None


class ConversionCallbackRequest(BaseModel):
    job_id: int
    filename: str
    html_key: str
    success: bool
    error: Optional[str] = None
