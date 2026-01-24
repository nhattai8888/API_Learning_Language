import uuid
from sqlalchemy import ForeignKey, Index, Integer, UniqueConstraint, String, Boolean, Text, Enum
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func

class UserReviewSettings(Base):
    __tablename__ = "user_review_settings"
    __table_args__ = (UniqueConstraint("user_id", "language_id", name="uq_user_review_settings"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)
    daily_new_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    daily_review_limit: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ReviewAttempt(Base):
    __tablename__ = "review_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)
    lexeme_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False)

    mode: Mapped[str] = mapped_column(String(24), nullable=False)  # keep string for DB compat
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user_answer: Mapped[str | None] = mapped_column(Text)
    expected: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

Index("idx_review_attempts_user_lang_time", ReviewAttempt.user_id, ReviewAttempt.language_id, ReviewAttempt.created_at.desc())
Index("idx_review_attempts_user_lexeme_time", ReviewAttempt.user_id, ReviewAttempt.lexeme_id, ReviewAttempt.created_at.desc())