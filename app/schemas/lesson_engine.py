from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.core.enums import LessonItemType, AttemptStatus


class ChoiceCreate(BaseModel):
    key: str = Field(min_length=1, max_length=32)
    text: str
    is_correct: bool = False
    sort_order: int = 0

class ChoiceOut(ChoiceCreate):
    id: UUID


# ---------- Items ----------
class LessonItemCreate(BaseModel):
    lesson_id: UUID
    item_type: LessonItemType
    prompt: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    correct_answer: Optional[Dict[str, Any]] = None
    points: int = 1
    sort_order: int = 0
    choices: Optional[List[ChoiceCreate]] = None  # only for MCQ/LISTEN

class LessonItemUpdate(BaseModel):
    prompt: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    correct_answer: Optional[Dict[str, Any]] = None
    points: Optional[int] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None
    # replace choices fully (optional)
    choices: Optional[List[ChoiceCreate]] = None

class LessonItemOut(BaseModel):
    id: UUID
    lesson_id: UUID
    item_type: LessonItemType
    prompt: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    points: int
    sort_order: int
    status: str
    choices: Optional[List[ChoiceOut]] = None


# ---------- Attempts ----------
class AttemptStartResponse(BaseModel):
    attempt_id: UUID
    lesson_id: UUID
    items: List[LessonItemOut]

class AnswerPayload(BaseModel):
    # flexible: depends on item_type
    answer: Any
    meta: Optional[Dict[str, Any]] = None

class AttemptSubmitRequest(BaseModel):
    # { "item_id": { "answer": ..., "meta": {...} } }
    answers: Dict[str, AnswerPayload]
    duration_sec: int = 0

class ItemResult(BaseModel):
    item_id: UUID
    is_correct: bool
    earned_points: int
    max_points: int
    detail: Optional[Dict[str, Any]] = None

class AttemptSubmitResponse(BaseModel):
    attempt_id: UUID
    status: AttemptStatus
    score_points: int
    max_points: int
    score_percent: int
    results: List[ItemResult]
    
class AttemptOut(BaseModel):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    status: AttemptStatus
    started_at: Any
    submitted_at: Optional[Any] = None
    score_points: int
    max_points: int
    score_percent: int
    duration_sec: int
    answers: Optional[Dict[str, Any]] = None
    result_breakdown: Optional[Dict[str, Any]] = None

class AttemptsListResponse(BaseModel):
    items: List[AttemptOut]
    total: int

# ---- AI scoring payload (for SPEAK items) ----
class SpeakItemAIResult(BaseModel):
    pronunciation: int = Field(ge=0, le=100)
    fluency: int = Field(ge=0, le=100)
    accuracy: int = Field(ge=0, le=100)
    words: Optional[List[Dict[str, Any]]] = None  # per-word errors, optional

class AttemptAIUpdateRequest(BaseModel):
    # map: item_id -> ai_result
    speak_results: Dict[str, SpeakItemAIResult]
    # optional: recompute total score policy
    finalize: bool = True

class AttemptAIUpdateResponse(BaseModel):
    attempt_id: UUID
    status: AttemptStatus
    score_points: int
    max_points: int
    score_percent: int