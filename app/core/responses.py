from typing import Any, Optional
from pydantic import BaseModel

class ApiResponse(BaseModel):
    code: int = 200
    data: Any = None
    message: str = ""

class ApiError(BaseModel):
    code:int = 400
    message: str
    data: Optional[Any] = None
