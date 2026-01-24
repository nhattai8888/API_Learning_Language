# app/schemas/grammar.py
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from app.models.grammar_engine import (
    GrammarStatus,
    GrammarDifficulty,
    GrammarExerciseType,
    GrammarMastery,
)


# -----------------------------
# Topic
# -----------------------------
class GrammarTopicCreate(BaseModel):
    language_id: UUID
    title: str = Field(min_length=1, max_length=180)
    slug: str = Field(min_length=1, max_length=180)
    description: Optional[str] = None
    sort_order: int = 0
    status: GrammarStatus = GrammarStatus.PUBLISHED


class GrammarTopicUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=180)
    slug: Optional[str] = Field(default=None, max_length=180)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[GrammarStatus] = None


class GrammarTopicOut(BaseModel):
    id: UUID
    language_id: UUID
    title: str
    slug: str
    description: Optional[str] = None
    sort_order: int
    status: GrammarStatus
    created_at: datetime


# -----------------------------
# Pattern
# -----------------------------
class GrammarPatternCreate(BaseModel):
    language_id: UUID
    topic_id: Optional[UUID] = None

    title: str = Field(min_length=1, max_length=220)
    short_rule: Optional[str] = None
    full_explanation: Optional[str] = None
    formula: Optional[Dict[str, Any]] = None
    common_mistakes: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None

    difficulty: GrammarDifficulty = GrammarDifficulty.EASY
    status: GrammarStatus = GrammarStatus.PUBLISHED


class GrammarPatternUpdate(BaseModel):
    topic_id: Optional[UUID] = None
    title: Optional[str] = Field(default=None, max_length=220)
    short_rule: Optional[str] = None
    full_explanation: Optional[str] = None
    formula: Optional[Dict[str, Any]] = None
    common_mistakes: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    difficulty: Optional[GrammarDifficulty] = None
    status: Optional[GrammarStatus] = None


class GrammarPatternOut(BaseModel):
    id: UUID
    language_id: UUID
    topic_id: Optional[UUID] = None
    title: str
    short_rule: Optional[str] = None
    full_explanation: Optional[str] = None
    formula: Optional[Dict[str, Any]] = None
    common_mistakes: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    difficulty: GrammarDifficulty
    status: GrammarStatus
    created_at: datetime
    updated_at: datetime


# -----------------------------
# Example
# -----------------------------
class GrammarExampleCreate(BaseModel):
    pattern_id: UUID
    sentence: str = Field(min_length=1)
    translation: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    highlight: Optional[Dict[str, Any]] = None


class GrammarExampleUpdate(BaseModel):
    sentence: Optional[str] = None
    translation: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    highlight: Optional[Dict[str, Any]] = None


class GrammarExampleOut(BaseModel):
    id: UUID
    pattern_id: UUID
    sentence: str
    translation: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    highlight: Optional[Dict[str, Any]] = None
    created_at: datetime


# -----------------------------
# Exercise + Choices
# -----------------------------
class GrammarExerciseCreate(BaseModel):
    pattern_id: UUID
    exercise_type: GrammarExerciseType
    prompt: str = Field(min_length=1)
    data: Optional[Dict[str, Any]] = None
    answer: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    difficulty: GrammarDifficulty = GrammarDifficulty.EASY


class GrammarExerciseUpdate(BaseModel):
    exercise_type: Optional[GrammarExerciseType] = None
    prompt: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    answer: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    difficulty: Optional[GrammarDifficulty] = None


class GrammarExerciseOut(BaseModel):
    id: UUID
    pattern_id: UUID
    exercise_type: GrammarExerciseType
    prompt: str
    data: Optional[Dict[str, Any]] = None
    answer: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    difficulty: GrammarDifficulty
    created_at: datetime


class GrammarChoiceCreate(BaseModel):
    exercise_id: UUID
    text: str = Field(min_length=1)
    is_correct: bool = False
    sort_order: int = 0


class GrammarChoiceUpdate(BaseModel):
    text: Optional[str] = None
    is_correct: Optional[bool] = None
    sort_order: Optional[int] = None


class GrammarChoiceOut(BaseModel):
    id: UUID
    exercise_id: UUID
    text: str
    is_correct: bool
    sort_order: int


# -----------------------------
# Lesson attach
# -----------------------------
class AttachGrammarToLessonRequest(BaseModel):
    lesson_id: UUID
    patterns: List[Dict[str, Any]]  # [{pattern_id, is_core, sort_order}]


class LessonGrammarOut(BaseModel):
    lesson_id: UUID
    pattern_id: UUID
    is_core: bool
    sort_order: int


# -----------------------------
# Grammar SRS session
# -----------------------------
class GrammarSessionItem(BaseModel):
    pattern: GrammarPatternOut
    examples: List[GrammarExampleOut] = []
    exercise: Optional[GrammarExerciseOut] = None
    choices: List[GrammarChoiceOut] = []
    state: Dict[str, Any]


class GrammarSessionResponse(BaseModel):
    session_id: str
    items: List[GrammarSessionItem]
    total: int


class GrammarSubmitItem(BaseModel):
    pattern_id: UUID
    exercise_id: Optional[UUID] = None
    user_answer: Optional[Dict[str, Any]] = None  # flexible for different types


class GrammarSubmitRequest(BaseModel):
    language_id: UUID
    session_id: str
    items: List[GrammarSubmitItem]


class GrammarSubmitResultItem(BaseModel):
    pattern_id: UUID
    is_correct: bool
    score_percent: int
    rating: int
    mastery: GrammarMastery
    familiarity: int
    next_review_at: Optional[datetime] = None


class GrammarSubmitResponse(BaseModel):
    updated: List[GrammarSubmitResultItem]
    count: int
