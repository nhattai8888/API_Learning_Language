import uuid
from sqlalchemy import String, Integer, Text, Boolean, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.models.base import Base
from app.core.enums import (
    EntityStatus, LexemeType, PublishStatus, WordDomain,
    WordMastery, WordErrorType, WordErrorSource, Severity
)

class Lexeme(Base):
    __tablename__ = "lexemes"
    __table_args__ = (
        UniqueConstraint("language_id", "lemma", "type", name="uq_lexemes_lang_lemma_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)

    type: Mapped[LexemeType] = mapped_column(Enum(LexemeType, name="lexeme_type_enum"), nullable=False, default=LexemeType.OTHER)
    lemma: Mapped[str] = mapped_column(String(180), nullable=False)

    # keep your existing field name
    phonetic: Mapped[str | None] = mapped_column(String(140))
    audio_url: Mapped[str | None] = mapped_column(Text)

    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB)

    status: Mapped[EntityStatus] = mapped_column(Enum(EntityStatus, name="entity_status_enum"), default=EntityStatus.ACTIVE, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


Index("idx_lexemes_language", Lexeme.language_id)
Index("idx_lexemes_language_difficulty", Lexeme.language_id, Lexeme.difficulty)


class WordSense(Base):
    __tablename__ = "word_senses"
    __table_args__ = (
        UniqueConstraint("lexeme_id", "sense_index", name="uq_word_senses_lexeme_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lexeme_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False)

    sense_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[WordDomain] = mapped_column(Enum(WordDomain, name="word_domain_enum"), default=WordDomain.OTHER, nullable=False)

    cefr_level: Mapped[str | None] = mapped_column(String(10))
    translations: Mapped[dict | None] = mapped_column(JSONB)     # {"vi": "...", "zh": "..."}
    collocations: Mapped[dict | None] = mapped_column(JSONB)     # [{"text":"make a decision"}]

    status: Mapped[PublishStatus] = mapped_column(Enum(PublishStatus, name="publish_status_enum"), default=PublishStatus.DRAFT, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


Index("idx_word_senses_lexeme", WordSense.lexeme_id)
Index("idx_word_senses_domain", WordSense.domain)


class WordExample(Base):
    __tablename__ = "word_examples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sense_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("word_senses.id", ondelete="CASCADE"), nullable=False)

    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    translation: Mapped[dict | None] = mapped_column(JSONB)
    audio_url: Mapped[str | None] = mapped_column(Text)

    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("idx_word_examples_sense", WordExample.sense_id)
Index("idx_word_examples_sense_diff", WordExample.sense_id, WordExample.difficulty)


class LessonLexeme(Base):
    __tablename__ = "lesson_lexemes"

    lesson_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    lexeme_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lexemes.id", ondelete="CASCADE"), primary_key=True)

    is_core: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


Index("idx_lesson_lexemes_lesson", LessonLexeme.lesson_id, LessonLexeme.sort_order)
Index("idx_lesson_lexemes_lexeme", LessonLexeme.lexeme_id)


class UserLexemeState(Base):
    __tablename__ = "user_lexeme_states"
    __table_args__ = (
        UniqueConstraint("user_id", "lexeme_id", name="uq_user_lexeme"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lexeme_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False)

    mastery: Mapped[WordMastery] = mapped_column(Enum(WordMastery, name="word_mastery_enum"), default=WordMastery.NEW, nullable=False)
    familiarity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0..100

    ease_factor: Mapped[float] = mapped_column(NUMERIC(4, 2), default=2.50, nullable=False)
    repetition: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapse_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    last_source: Mapped[WordErrorSource | None] = mapped_column(Enum(WordErrorSource, name="word_error_source_enum"))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


Index("idx_user_lexeme_next_review", UserLexemeState.user_id, UserLexemeState.next_review_at)
Index("idx_user_lexeme_mastery", UserLexemeState.user_id, UserLexemeState.mastery)


class UserWordError(Base):
    __tablename__ = "user_word_errors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lexeme_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False)

    error_type: Mapped[WordErrorType] = mapped_column(Enum(WordErrorType, name="word_error_type_enum"), default=WordErrorType.OTHER, nullable=False)
    source: Mapped[WordErrorSource] = mapped_column(Enum(WordErrorSource, name="word_error_source_enum"), default=WordErrorSource.OTHER, nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity, name="severity_enum"), default=Severity.OK, nullable=False)

    occur_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    evidence: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("idx_user_word_errors_user", UserWordError.user_id, UserWordError.last_occurred_at)
Index("idx_user_word_errors_user_lexeme", UserWordError.user_id, UserWordError.lexeme_id)
Index("idx_user_word_errors_hot", UserWordError.user_id, UserWordError.severity, UserWordError.last_occurred_at)
