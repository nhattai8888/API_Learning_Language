from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from app.core.enums import EntityStatus, LexemeType, PublishStatus, WordDomain, WordMastery, WordErrorType, WordErrorSource, Severity

# ---- Lexeme ----
class LexemeCreate(BaseModel):
    language_id: UUID
    type: LexemeType
    lemma: str = Field(min_length=1, max_length=180)
    phoenic: Optional[str] = None
    audio_url: Optional[str] = None
    difficulty: int = Field(default=1, ge=1, le=10)
    tags: Optional[Dict[str, Any]] = None

class LexemeUpdate(BaseModel):
    type: Optional[LexemeType] = None
    lemma: Optional[str] = Field(default=None, max_length=180)
    phoenic: Optional[str] = None
    audio_url: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=10)
    tags: Optional[Dict[str, Any]] = None
    status: Optional[EntityStatus] = None

class LexemeOut(BaseModel):
    id: UUID
    language_id: UUID
    type: LexemeType
    lemma: str
    phoenic: Optional[str] = None
    audio_url: Optional[str] = None
    difficulty: int
    tags: Optional[Dict[str, Any]] = None
    status: EntityStatus
    created_at: datetime
    updated_at: datetime


# ---- Sense ----
class SenseCreate(BaseModel):
    lexeme_id: UUID
    sense_index: int = 1
    definition: str
    domain: WordDomain = WordDomain.OTHER
    cefr_level: Optional[str] = None
    translations: Optional[Dict[str, Any]] = None
    collocations: Optional[Dict[str, Any]] = None
    status: PublishStatus = PublishStatus.DRAFT

class SenseUpdate(BaseModel):
    sense_index: Optional[int] = None
    definition: Optional[str] = None
    domain: Optional[WordDomain] = None
    cefr_level: Optional[str] = None
    translations: Optional[Dict[str, Any]] = None
    collocations: Optional[Dict[str, Any]] = None
    status: Optional[PublishStatus] = None

class SenseOut(BaseModel):
    id: UUID
    lexeme_id: UUID
    sense_index: int
    definition: str
    domain: WordDomain
    cefr_level: Optional[str] = None
    translations: Optional[Dict[str, Any]] = None
    collocations: Optional[Dict[str, Any]] = None
    status: PublishStatus
    created_at: datetime
    updated_at: datetime


# ---- Example ----
class ExampleCreate(BaseModel):
    sense_id: UUID
    sentence: str
    translation: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    difficulty: int = Field(default=1, ge=1, le=10)
    tags: Optional[Dict[str, Any]] = None

class ExampleUpdate(BaseModel):
    sentence: Optional[str] = None
    translation: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=10)
    tags: Optional[Dict[str, Any]] = None

class ExampleOut(BaseModel):
    id: UUID
    sense_id: UUID
    sentence: str
    translation: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    difficulty: int
    tags: Optional[Dict[str, Any]] = None
    created_at: datetime


# ---- Lesson link ----
class AttachLexemesToLessonRequest(BaseModel):
    lesson_id: UUID
    lexemes: List[Dict[str, Any]]  # [{lexeme_id, is_core, sort_order}]

class LessonLexemeOut(BaseModel):
    lesson_id: UUID
    lexeme_id: UUID
    is_core: bool
    sort_order: int


# ---- SRS Review ----
class ReviewCard(BaseModel):
    lexeme: LexemeOut
    senses: List[SenseOut] = []
    examples: List[ExampleOut] = []
    state: Dict[str, Any]  # familiarity/mastery/next_review_at...

class ReviewTodayResponse(BaseModel):
    items: List[ReviewCard]
    total: int

class ReviewResultRequest(BaseModel):
    lexeme_id: UUID
    rating: int = Field(ge=0, le=5)  # 0 fail .. 5 perfect
    source: WordErrorSource = WordErrorSource.QUIZ


# ---- Weak words ----
class WeakWordOut(BaseModel):
    lexeme_id: UUID
    lemma: str
    type: LexemeType
    severity: Severity
    error_type: WordErrorType
    occur_count: int
    last_occurred_at: datetime
    evidence: Optional[Dict[str, Any]] = None
