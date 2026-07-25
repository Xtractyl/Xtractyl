# orchestrator/api/contracts/conversion.py

import re
from typing import List, Optional

from pydantic import BaseModel, field_validator


class PrepareConversionRequest(BaseModel):
    project: str
    filenames: List[str]

    @field_validator("project")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 3:
            raise ValueError("project name must be at least 3 characters")
        if not re.fullmatch(r"[A-Za-z0-9_]+", v):
            raise ValueError("project name may only contain letters, numbers, and underscores")
        return v

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


class DiscardConversionRequest(BaseModel):
    job_id: int


class DiscardConversionResponse(BaseModel):
    status: str


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
    pdf_hash: Optional[str] = None
    html_hash: Optional[str] = None


class ConversionCallbackResponse(BaseModel):
    status: str
