"""Common pydantic response schemas (placeholders)"""
from pydantic import BaseModel
from typing import Any, Optional


class ResponseSchema(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
