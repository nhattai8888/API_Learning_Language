import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import String, Integer, ForeignKey, Enum, Text, Boolean, Index
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func

from app.models.base import Base
from app.core.enums import SpeakingTaskType, SpeakingAttemptStatus, SpeakingItemType


class SpeakingTask(Base):
    __tablename__ = "speaking_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)

    task_type: Mapped[SpeakingTaskType] = mapped_column(Enum(SpeakingTaskType, name="speaking_task_type_enum"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # Prompt content
    prompt_text: Mapped[str | None] = mapped_column(Text)
    prompt_audio_url: Mapped[str | None] = mapped_column(Text)
    reference_text: Mapped[str | None] = mapped_column(Text)  # read aloud / repeat expected
    picture_url: Mapped[str | None] = mapped_column(Text)

    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB)

    status: Mapped[str] = mapped_column(String(16), default="PUBLISHED", nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("idx_speaking_tasks_lang_type", SpeakingTask.language_id, SpeakingTask.task_type)


class SpeakingAttempt(Base):
    __tablename__ = "speaking_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("speaking_tasks.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[SpeakingAttemptStatus] = mapped_column(Enum(SpeakingAttemptStatus, name="speaking_attempt_status_enum"), default=SpeakingAttemptStatus.STARTED, nullable=False)

    duration_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submitted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    # scoring summary
    score_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0..100
    band: Mapped[float | None] = mapped_column(String(8))  # optional (IELTS-like mapping if you want)

    # full payloads
    answers: Mapped[dict | None] = mapped_column(JSONB)               # {item_id: {audio_url/audio_base64...}}
    ai_result: Mapped[dict | None] = mapped_column(JSONB)             # {transcript, word_feedback, pronunciation..}
    error: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


Index("idx_speaking_attempt_user_time", SpeakingAttempt.user_id, SpeakingAttempt.created_at.desc())
Index("idx_speaking_attempt_status", SpeakingAttempt.status)


class SpeakingAttemptItem(Base):
    __tablename__ = "speaking_attempt_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("speaking_attempts.id", ondelete="CASCADE"), nullable=False)

    item_type: Mapped[SpeakingItemType] = mapped_column(Enum(SpeakingItemType, name="speaking_item_type_enum"), default=SpeakingItemType.SPEAK, nullable=False)

    prompt_text: Mapped[str | None] = mapped_column(Text)
    reference_text: Mapped[str | None] = mapped_column(Text)  # expected transcript for read/repeat
    prompt_audio_url: Mapped[str | None] = mapped_column(Text)
    picture_url: Mapped[str | None] = mapped_column(Text)

    # user submission
    audio_url: Mapped[str | None] = mapped_column(Text)
    audio_mime: Mapped[str | None] = mapped_column(String(64))
    audio_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # scoring per item
    ai_score: Mapped[dict | None] = mapped_column(JSONB)  # {pronunciation, fluency, accuracy, transcript, word_feedback, tips...}
    is_scored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("idx_speaking_attempt_items_attempt", SpeakingAttemptItem.attempt_id)
