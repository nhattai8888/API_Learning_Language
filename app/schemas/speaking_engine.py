from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from app.core.enums import SpeakingTaskType, SpeakingAttemptStatus


# -------- Tasks (admin/teacher authoring) --------
class SpeakingTaskCreate(BaseModel):
    language_id: UUID
    task_type: SpeakingTaskType
    title: str = Field(min_length=1, max_length=200)

    prompt_text: Optional[str] = None
    prompt_audio_url: Optional[str] = None
    reference_text: Optional[str] = None
    picture_url: Optional[str] = None

    difficulty: int = Field(default=1, ge=1, le=10)
    tags: Optional[Dict[str, Any]] = None
    status: str = "PUBLISHED"


class SpeakingTaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    prompt_text: Optional[str] = None
    prompt_audio_url: Optional[str] = None
    reference_text: Optional[str] = None
    picture_url: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=10)
    tags: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class SpeakingTaskOut(BaseModel):
    id: UUID
    language_id: UUID
    task_type: SpeakingTaskType
    title: str
    prompt_text: Optional[str] = None
    prompt_audio_url: Optional[str] = None
    reference_text: Optional[str] = None
    picture_url: Optional[str] = None
    difficulty: int
    tags: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime


# -------- Attempt flow --------
class StartSpeakingAttemptRequest(BaseModel):
    language_id: UUID
    task_id: UUID


class SpeakingAttemptItemOut(BaseModel):
    id: UUID
    prompt_text: Optional[str] = None
    prompt_audio_url: Optional[str] = None
    reference_text: Optional[str] = None
    picture_url: Optional[str] = None


class StartSpeakingAttemptResponse(BaseModel):
    attempt_id: UUID
    task_id: UUID
    status: SpeakingAttemptStatus
    items: List[SpeakingAttemptItemOut]


class SubmitSpeakingAttemptItem(BaseModel):
    item_id: UUID
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None  # if you allow direct upload
    audio_mime: str = "audio/wav"
    duration_ms: int = 0


class SubmitSpeakingAttemptRequest(BaseModel):
    duration_sec: int = 0
    items: List[SubmitSpeakingAttemptItem]
    strictness: int = Field(default=75, ge=0, le=100)  # ELSA-like strictness


class SpeakingAttemptOut(BaseModel):
    id: UUID
    user_id: UUID
    language_id: UUID
    task_id: UUID
    status: SpeakingAttemptStatus
    duration_sec: int
    submitted_at: Optional[datetime] = None
    score_percent: int
    ai_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class SpeakingScoreOut(BaseModel):
    attempt_id: UUID
    status: SpeakingAttemptStatus
    score_percent: int
    ai_result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
