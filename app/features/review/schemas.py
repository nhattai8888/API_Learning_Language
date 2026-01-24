from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from app.core.enums import ReviewMode, WordErrorSource, WordMastery

class ReviewSettingsUpsert(BaseModel):
    language_id: UUID
    daily_new_limit: int = Field(default=10, ge=0, le=200)
    daily_review_limit: int = Field(default=50, ge=0, le=500)

class ReviewSettingsOut(BaseModel):
    language_id: UUID
    daily_new_limit: int
    daily_review_limit: int

class ReviewCard(BaseModel):
    lexeme_id: UUID
    lemma: str
    type: str
    phonetic: Optional[str] = None
    audio_url: Optional[str] = None
    difficulty: int = 1
    tags: Optional[Dict[str, Any]] = None

    mastery: WordMastery
    familiarity: int
    next_review_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None

    senses: List[Dict[str, Any]] = []
    examples: List[Dict[str, Any]] = []
    weak_notes: Optional[List[Dict[str, Any]]] = None  # from user_word_errors

class ReviewTodayResponse(BaseModel):
    items: List[ReviewCard]
    total: int
    due_count: int
    new_count: int

class ReviewSubmitItem(BaseModel):
    lexeme_id: UUID
    rating: int = Field(ge=0, le=5)  # 0 fail..5 perfect
    source: WordErrorSource = WordErrorSource.QUIZ

class ReviewSubmitRequest(BaseModel):
    language_id: UUID
    items: List[ReviewSubmitItem]

class ReviewSubmitResultItem(BaseModel):
    lexeme_id: UUID
    mastery: WordMastery
    familiarity: int
    ease_factor: float
    repetition: int
    interval_days: int
    next_review_at: Optional[datetime] = None

class ReviewSubmitResponse(BaseModel):
    updated: List[ReviewSubmitResultItem]
    count: int

class ReviewStatsResponse(BaseModel):
    language_id: UUID
    due_now: int
    scheduled_total: int
    mastered: int
    learning: int
    avg_familiarity: int
    reviewed_7d: int

class ReviewSessionItem(BaseModel):
    lexeme_id: UUID
    mode: ReviewMode
    prompt: Dict[str, Any]          # data for UI
    expected: Optional[Dict[str, Any]] = None  # optional client-side checks

class ReviewSessionResponse(BaseModel):
    session_id: str
    mode: ReviewMode
    items: List[ReviewSessionItem]
    total: int

class ReviewSessionSubmitItem(BaseModel):
    lexeme_id: UUID
    mode: ReviewMode
    user_answer: Optional[str] = None
    choice_id: Optional[str] = None
    know: Optional[bool] = None                 # flashcard
    duration_ms: Optional[int] = None
    audio_base64: Optional[str] = None          # shadowing
    mime_type: Optional[str] = "audio/wav"

class ReviewSessionSubmitRequest(BaseModel):
    language_id: UUID
    session_id: str
    items: List[ReviewSessionSubmitItem]

class ReviewSessionSubmitResult(BaseModel):
    lexeme_id: UUID
    score_percent: int
    rating: int
    is_correct: bool
    next_review_at: Optional[datetime] = None
    mastery: WordMastery
    familiarity: int
    meta: Optional[Dict[str, Any]] = None

class ReviewSessionSubmitResponse(BaseModel):
    updated: List[ReviewSessionSubmitResult]
    count: int