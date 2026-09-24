# worker_conversion/contracts.py
from __future__ import annotations

from pydantic import BaseModel


class ConversionJobPayload(BaseModel):
    job_id: int
    project: str
    pdf_keys: list[str]
