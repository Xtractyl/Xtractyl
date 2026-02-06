# orchestrator/api/contracts/errors.py
from typing import List, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    loc: Optional[List[str]] = None
    msg: str
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable safe message")
    request_id: Optional[str] = None
    details: Optional[List[ErrorDetail]] = None
