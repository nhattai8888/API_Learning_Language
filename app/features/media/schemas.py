import enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class MediaProvider(enum.Enum):
    GDRIVE = "GDRIVE"

class MediaStatus(enum.Enum):
    INIT = "INIT"
    UPLOADING = "UPLOADING"
    READY = "READY"
    FAILED = "FAILED"

class CreateUploadSessionRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(default="audio/wav", max_length=128)
    size_bytes: int = Field(ge=1, le=50_000_000)  # 50MB limit (tune)
    metadata: Optional[Dict[str, Any]] = None     # optional: {attempt_id, item_id}

class CreateUploadSessionResponse(BaseModel):
    upload_url: str
    media_id: UUID
    provider: str = "GDRIVE"
    status: str = "UPLOADING"

class FinalizeUploadRequest(BaseModel):
    media_id: UUID
    drive_file_id: str = Field(min_length=5)
    size_bytes: Optional[int] = None

class MediaOut(BaseModel):
    id: UUID
    provider: str
    status: str
    file_name: str
    mime_type: str
    size_bytes: int
    drive_file_id: Optional[str] = None
    drive_view_url: Optional[str] = None
    created_at: datetime
