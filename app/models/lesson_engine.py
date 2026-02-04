import uuid
from sqlalchemy import String, Integer, Text, Boolean, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.models.base import Base
from app.core.enums import EntityStatus, LessonItemType, LessonProgressStatus, AttemptStatus


class LessonItem(Base):
    __tablename__ = "lesson_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)

    item_type: Mapped[LessonItemType] = mapped_column(Enum(LessonItemType, name="lesson_item_type_enum"), nullable=False)

    prompt: Mapped[str | None] = mapped_column(Text)
    # content: audio_url, transcript, options, etc.
    content: Mapped[dict | None] = mapped_column(JSONB)
    # correct_answer format depends on item_type
    answer: Mapped[dict | None] = mapped_column(JSONB)

    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[EntityStatus] = mapped_column(Enum(EntityStatus, name="entity_status_enum"), default=EntityStatus.ACTIVE, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("idx_lesson_items_lesson_sort", LessonItem.lesson_id, LessonItem.sort_order)


class LessonItemChoice(Base):
    __tablename__ = "lesson_item_choices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lesson_items.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(32), nullable=False)   # "A","B","C" or uuid short
    text_value: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


Index("idx_choices_item_sort", LessonItemChoice.item_id, LessonItemChoice.sort_order)
Index("idx_choices_item_key", LessonItemChoice.item_id, LessonItemChoice.key)


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[LessonProgressStatus] = mapped_column(
        Enum(LessonProgressStatus, name="lesson_progress_status_enum"),
        default=LessonProgressStatus.NOT_STARTED,
        nullable=False,
    )
    last_item_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_score: Mapped[float] = mapped_column(Integer, default=0, nullable=False)  # store % as int (0-100) for speed
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


Index("idx_progress_user_lesson", UserLessonProgress.user_id, UserLessonProgress.lesson_id, unique=True)


class LessonAttempt(Base):
    __tablename__ = "lesson_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[AttemptStatus] = mapped_column(Enum(AttemptStatus, name="attempt_status_enum"), default=AttemptStatus.STARTED, nullable=False)

    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submitted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    score_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100

    duration_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # answers saved as JSONB: { item_id: {answer:..., meta:...}, ... }
    answers: Mapped[dict | None] = mapped_column(JSONB)
    # breakdown saved as JSONB for review
    result_breakdown: Mapped[dict | None] = mapped_column(JSONB)


Index("idx_attempts_user_lesson", LessonAttempt.user_id, LessonAttempt.lesson_id)
Index("idx_attempts_lesson_started", LessonAttempt.lesson_id, LessonAttempt.started_at)
