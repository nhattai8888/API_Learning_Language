import uuid
from sqlalchemy import NUMERIC, String, Integer, Text, Boolean, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.enums import GrammarDifficulty, GrammarExerciseType, GrammarMastery, GrammarStatus
from app.models.base import Base
class GrammarTopic(Base):
    __tablename__ = "grammar_topics"
    __table_args__ = (UniqueConstraint("language_id","slug", name="uq_grammar_topics_lang_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[GrammarStatus] = mapped_column(Enum(GrammarStatus, name="grammar_status_enum"), default=GrammarStatus.PUBLISHED, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

Index("idx_grammar_topics_lang", GrammarTopic.language_id, GrammarTopic.sort_order)


class GrammarPattern(Base):
    __tablename__ = "grammar_patterns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("grammar_topics.id", ondelete="SET NULL"))

    title: Mapped[str] = mapped_column(String(220), nullable=False)
    short_rule: Mapped[str | None] = mapped_column(Text)
    full_explanation: Mapped[str | None] = mapped_column(Text)
    formula: Mapped[dict | None] = mapped_column(JSONB)
    common_mistakes: Mapped[dict | None] = mapped_column(JSONB)
    tags: Mapped[dict | None] = mapped_column(JSONB)

    difficulty: Mapped[GrammarDifficulty] = mapped_column(Enum(GrammarDifficulty, name="grammar_difficulty_enum"), default=GrammarDifficulty.EASY, nullable=False)
    status: Mapped[GrammarStatus] = mapped_column(Enum(GrammarStatus, name="grammar_status_enum"), default=GrammarStatus.PUBLISHED, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

Index("idx_grammar_patterns_lang_topic", GrammarPattern.language_id, GrammarPattern.topic_id)


class GrammarExample(Base):
    __tablename__ = "grammar_examples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grammar_patterns.id", ondelete="CASCADE"), nullable=False)
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    translation: Mapped[dict | None] = mapped_column(JSONB)
    audio_url: Mapped[str | None] = mapped_column(Text)
    highlight: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

Index("idx_grammar_examples_pattern", GrammarExample.pattern_id)


class GrammarExercise(Base):
    __tablename__ = "grammar_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grammar_patterns.id", ondelete="CASCADE"), nullable=False)

    exercise_type: Mapped[GrammarExerciseType] = mapped_column(Enum(GrammarExerciseType, name="grammar_exercise_type_enum"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB)
    answer: Mapped[dict | None] = mapped_column(JSONB)
    explanation: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[GrammarDifficulty] = mapped_column(Enum(GrammarDifficulty, name="grammar_difficulty_enum"), default=GrammarDifficulty.EASY, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

Index("idx_grammar_exercises_pattern", GrammarExercise.pattern_id)


class GrammarChoice(Base):
    __tablename__ = "grammar_choices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grammar_exercises.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

Index("idx_grammar_choices_ex", GrammarChoice.exercise_id, GrammarChoice.sort_order)


class LessonGrammarPattern(Base):
    __tablename__ = "lesson_grammar_patterns"

    lesson_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    pattern_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grammar_patterns.id", ondelete="CASCADE"), primary_key=True)
    is_core: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

Index("idx_lesson_grammar_patterns_lesson", LessonGrammarPattern.lesson_id, LessonGrammarPattern.sort_order)


class UserGrammarState(Base):
    __tablename__ = "user_grammar_states"
    __table_args__ = (UniqueConstraint("user_id","pattern_id", name="uq_user_pattern"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pattern_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grammar_patterns.id", ondelete="CASCADE"), nullable=False)

    mastery: Mapped[GrammarMastery] = mapped_column(Enum(GrammarMastery, name="grammar_mastery_enum"), default=GrammarMastery.NEW, nullable=False)
    familiarity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ease_factor: Mapped[float] = mapped_column(NUMERIC(4,2), default=2.50, nullable=False)
    repetition: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapse_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

Index("idx_user_grammar_next_review", UserGrammarState.user_id, UserGrammarState.next_review_at)


class GrammarAttempt(Base):
    __tablename__ = "grammar_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)
    pattern_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grammar_patterns.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("grammar_exercises.id", ondelete="SET NULL"))

    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user_answer: Mapped[dict | None] = mapped_column(JSONB)
    meta: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

Index("idx_grammar_attempts_user_lang_time", GrammarAttempt.user_id, GrammarAttempt.language_id, GrammarAttempt.created_at.desc())