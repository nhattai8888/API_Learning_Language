from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from app.core.enums import LessonType, PublishStatus


# ---------- Language ----------
class LanguageCreate(BaseModel):
    code: str = Field(min_length=2, max_length=10)
    name: str = Field(min_length=2, max_length=50)
    script: Optional[str] = Field(default=None, max_length=20)

class LanguageUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    script: Optional[str] = Field(default=None, max_length=20)

class LanguageOut(BaseModel):
    id: UUID
    code: str
    name: str
    script: Optional[str] = None


# ---------- Level ----------
class LevelCreate(BaseModel):
    language_id: UUID
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)
    sort_order: int = 0

class LevelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    sort_order: Optional[int] = None

class LevelOut(BaseModel):
    id: UUID
    language_id: UUID
    code: str
    name: str
    sort_order: int


# ---------- Unit ----------
class UnitCreate(BaseModel):
    language_id: UUID
    level_id: Optional[UUID] = None
    title: str = Field(min_length=2, max_length=120)
    description: Optional[str] = None
    sort_order: int = 0

class UnitUpdate(BaseModel):
    level_id: Optional[UUID] = None
    title: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = None
    sort_order: Optional[int] = None

class UnitOut(BaseModel):
    id: UUID
    language_id: UUID
    level_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    sort_order: int


# ---------- Lesson ----------
class LessonCreate(BaseModel):
    language_id: UUID
    unit_id: Optional[UUID] = None
    title: str = Field(min_length=2, max_length=120)
    objective: Optional[str] = None
    estimated_minutes: int = 6
    lesson_type: LessonType = LessonType.STANDARD
    slug: str = Field(min_length=2, max_length=160)
    sort_order: int = 0

class LessonUpdate(BaseModel):
    unit_id: Optional[UUID] = None
    title: Optional[str] = Field(default=None, max_length=120)
    objective: Optional[str] = None
    estimated_minutes: Optional[int] = None
    lesson_type: Optional[LessonType] = None
    publish_status: Optional[PublishStatus] = None
    sort_order: Optional[int] = None

class LessonOut(BaseModel):
    id: UUID
    language_id: UUID
    unit_id: Optional[UUID] = None
    title: str
    objective: Optional[str] = None
    estimated_minutes: int
    lesson_type: LessonType
    publish_status: PublishStatus
    version: int
    slug: str
    sort_order: int
