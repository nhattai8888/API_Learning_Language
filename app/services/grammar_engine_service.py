from __future__ import annotations

import uuid as uuid_pkg
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.grammar_engine import (
    GrammarTopic,
    GrammarPattern,
    GrammarExample,
    GrammarExercise,
    GrammarChoice,
    LessonGrammarPattern,
    UserGrammarState,
    GrammarAttempt,
    GrammarStatus,
    GrammarMastery,
    GrammarExerciseType,
)

# -----------------------------
# Helpers
# -----------------------------
def _score_to_rating(score: int) -> int:
    if score >= 95:
        return 5
    if score >= 85:
        return 4
    if score >= 70:
        return 3
    if score >= 50:
        return 2
    if score >= 30:
        return 1
    return 0


def _sm2_update(state: UserGrammarState, rating: int):
    """
    Similar to vocab SRS, but for grammar patterns.
    """
    now = datetime.now(timezone.utc)
    ef = float(state.ease_factor or 2.5)
    rep = int(state.repetition or 0)
    interval = int(state.interval_days or 0)
    fam = int(state.familiarity or 0)

    if rating < 3:
        rep = 0
        interval = 1
        state.lapse_count = int(state.lapse_count or 0) + 1
        state.mastery = GrammarMastery.LEARNING
        fam = max(0, fam - 10)
    else:
        rep += 1
        if rep == 1:
            interval = 1
        elif rep == 2:
            interval = 3
        else:
            interval = max(1, int(round(interval * ef)))

        ef = ef + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        ef = min(2.8, max(1.3, ef))

        fam = min(100, fam + (6 + rating))
        if fam >= 85:
            state.mastery = GrammarMastery.MASTERED
        elif fam >= 60:
            state.mastery = GrammarMastery.KNOWN
        else:
            state.mastery = GrammarMastery.LEARNING

    state.ease_factor = ef
    state.repetition = rep
    state.interval_days = interval
    state.familiarity = fam
    state.last_reviewed_at = now
    state.next_review_at = now + timedelta(days=interval)
    state.updated_at = now


async def _ensure_state(db: AsyncSession, user_id: str, pattern_id: str) -> UserGrammarState:
    st = (await db.execute(
        select(UserGrammarState).where(UserGrammarState.user_id == user_id, UserGrammarState.pattern_id == pattern_id)
    )).scalar_one_or_none()
    if not st:
        st = UserGrammarState(user_id=user_id, pattern_id=pattern_id, mastery=GrammarMastery.NEW, familiarity=0, ease_factor=2.5)
        await db.add(st)
        await db.flush()
    return st


# -----------------------------
# CRUD Topic
# -----------------------------
async def create_topic(db: AsyncSession, payload):
    x = GrammarTopic(**payload.model_dump())
    await db.add(x)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("GRAMMAR_TOPIC_EXISTS")
    await db.refresh(x)
    return x


async def update_topic(db: AsyncSession, topic_id: str, payload):
    x = await db.get(GrammarTopic, topic_id)
    if not x:
        raise ValueError("GRAMMAR_TOPIC_NOT_FOUND")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(x, k, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("GRAMMAR_TOPIC_UPDATE_CONFLICT")

    await db.refresh(x)
    return x


async def get_topic(db: AsyncSession, topic_id: str):
    x = await db.get(GrammarTopic, topic_id)
    if not x:
        raise ValueError("GRAMMAR_TOPIC_NOT_FOUND")
    return x


async def list_topics(db: AsyncSession, language_id: str, status: str | None = None, limit: int = 50, offset: int = 0):
    stmt = select(GrammarTopic).where(GrammarTopic.language_id == language_id)
    if status:
        stmt = stmt.where(GrammarTopic.status == status)
    stmt = stmt.order_by(GrammarTopic.sort_order.asc(), GrammarTopic.title.asc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


# -----------------------------
# CRUD Pattern
# -----------------------------
async def create_pattern(db: AsyncSession, payload):
    x = GrammarPattern(**payload.model_dump())
    await db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def update_pattern(db: AsyncSession, pattern_id: str, payload):
    x = await db.get(GrammarPattern, pattern_id)
    if not x:
        raise ValueError("GRAMMAR_PATTERN_NOT_FOUND")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(x, k, v)

    await db.commit()
    await db.refresh(x)
    return x


async def get_pattern(db: AsyncSession, pattern_id: str):
    x = await db.get(GrammarPattern, pattern_id)
    if not x:
        raise ValueError("GRAMMAR_PATTERN_NOT_FOUND")
    return x


async def list_patterns(
    db: AsyncSession,
    language_id: str,
    topic_id: str | None = None,
    q: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    stmt = select(GrammarPattern).where(GrammarPattern.language_id == language_id)
    if topic_id:
        stmt = stmt.where(GrammarPattern.topic_id == topic_id)
    if status:
        stmt = stmt.where(GrammarPattern.status == status)
    if q:
        stmt = stmt.where(GrammarPattern.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(GrammarPattern.title.asc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


# -----------------------------
# CRUD Example
# -----------------------------
async def create_example(db: AsyncSession, payload):
    x = GrammarExample(**payload.model_dump())
    await db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def update_example(db: AsyncSession, example_id: str, payload):
    x = await db.get(GrammarExample, example_id)
    if not x:
        raise ValueError("GRAMMAR_EXAMPLE_NOT_FOUND")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(x, k, v)
    await db.commit()
    await db.refresh(x)
    return x


async def list_examples_by_pattern(db: AsyncSession, pattern_id: str, limit: int = 10):
    stmt = select(GrammarExample).where(GrammarExample.pattern_id == pattern_id).order_by(GrammarExample.created_at.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


# -----------------------------
# CRUD Exercise + Choice
# -----------------------------
async def create_exercise(db: AsyncSession, payload):
    x = GrammarExercise(**payload.model_dump())
    await db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def update_exercise(db: AsyncSession, exercise_id: str, payload):
    x = await db.get(GrammarExercise, exercise_id)
    if not x:
        raise ValueError("GRAMMAR_EXERCISE_NOT_FOUND")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(x, k, v)
    await db.commit()
    await db.refresh(x)
    return x


async def get_exercise(db: AsyncSession, exercise_id: str):
    x = await db.get(GrammarExercise, exercise_id)
    if not x:
        raise ValueError("GRAMMAR_EXERCISE_NOT_FOUND")
    return x


async def list_exercises_by_pattern(db: AsyncSession, pattern_id: str, limit: int = 50, offset: int = 0):
    stmt = select(GrammarExercise).where(GrammarExercise.pattern_id == pattern_id).order_by(GrammarExercise.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


async def create_choice(db: AsyncSession, payload):
    x = GrammarChoice(**payload.model_dump())
    await db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def update_choice(db: AsyncSession, choice_id: str, payload):
    x = await db.get(GrammarChoice, choice_id)
    if not x:
        raise ValueError("GRAMMAR_CHOICE_NOT_FOUND")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(x, k, v)
    await db.commit()
    await db.refresh(x)
    return x


async def list_choices(db: AsyncSession, exercise_id: str):
    stmt = select(GrammarChoice).where(GrammarChoice.exercise_id == exercise_id).order_by(GrammarChoice.sort_order.asc())
    return (await db.execute(stmt)).scalars().all()


# -----------------------------
# Lesson attach
# -----------------------------
async def attach_patterns_to_lesson(db: AsyncSession, lesson_id: str, patterns: list[dict[str, Any]]):
    await db.execute(delete(LessonGrammarPattern).where(LessonGrammarPattern.lesson_id == lesson_id))
    for it in patterns:
        await db.add(LessonGrammarPattern(
            lesson_id=lesson_id,
            pattern_id=it["pattern_id"],
            is_core=bool(it.get("is_core", True)),
            sort_order=int(it.get("sort_order", 0)),
        ))
    await db.commit()
    stmt = select(LessonGrammarPattern).where(LessonGrammarPattern.lesson_id == lesson_id).order_by(LessonGrammarPattern.sort_order.asc())
    return (await db.execute(stmt)).scalars().all()


async def list_lesson_patterns(db: AsyncSession, lesson_id: str):
    stmt = select(LessonGrammarPattern).where(LessonGrammarPattern.lesson_id == lesson_id).order_by(LessonGrammarPattern.sort_order.asc())
    return (await db.execute(stmt)).scalars().all()


# -----------------------------
# Grammar SRS session + submit
# -----------------------------
async def _pick_due_patterns(db: AsyncSession, user_id: str, language_id: str, limit: int):
    now = datetime.now(timezone.utc)
    stmt = (
        select(UserGrammarState)
        .join(GrammarPattern, GrammarPattern.id == UserGrammarState.pattern_id)
        .where(
            UserGrammarState.user_id == user_id,
            GrammarPattern.language_id == language_id,
            GrammarPattern.status == GrammarStatus.PUBLISHED,
            UserGrammarState.next_review_at.isnot(None),
            UserGrammarState.next_review_at <= now,
        )
        .order_by(UserGrammarState.next_review_at.asc().nullsfirst(), UserGrammarState.updated_at.asc())
        .limit(limit)
    )
    return (await db.execute(stmt)).scalars().all()


async def _pick_new_patterns(db: AsyncSession, user_id: str, language_id: str, limit: int):
    subq = select(UserGrammarState.pattern_id).where(UserGrammarState.user_id == user_id).subquery()
    stmt = (
        select(GrammarPattern)
        .where(
            GrammarPattern.language_id == language_id,
            GrammarPattern.status == GrammarStatus.PUBLISHED,
            ~GrammarPattern.id.in_(select(subq.c.pattern_id)),
        )
        .order_by(GrammarPattern.difficulty.asc(), GrammarPattern.title.asc())
        .limit(limit)
    )
    return (await db.execute(stmt)).scalars().all()


async def start_session(db: AsyncSession, user_id: str, language_id: str, limit: int = 10):
    """
    Strategy: due first, then new fill.
    """
    due_states = await _pick_due_patterns(db, user_id, language_id, limit=limit)
    due_ids = [str(s.pattern_id) for s in due_states]

    remaining = max(0, limit - len(due_ids))
    new_patterns = await _pick_new_patterns(db, user_id, language_id, limit=remaining)
    new_ids = [str(p.id) for p in new_patterns]

    # ensure states for new
    for p in new_patterns:
        await db.add(UserGrammarState(user_id=user_id, pattern_id=p.id, mastery=GrammarMastery.NEW, familiarity=0, ease_factor=2.5))
    if new_patterns:
        await db.commit()

    pattern_ids = due_ids + new_ids
    if not pattern_ids:
        return {"session_id": str(uuid_pkg.uuid4()), "items": [], "total": 0}

    patterns = (await db.execute(select(GrammarPattern).where(GrammarPattern.id.in_(pattern_ids)))).scalars().all()
    pmap = {str(p.id): p for p in patterns}

    states = (await db.execute(
        select(UserGrammarState).where(UserGrammarState.user_id == user_id, UserGrammarState.pattern_id.in_(pattern_ids))
    )).scalars().all()
    smap = {str(s.pattern_id): s for s in states}

    session_id = str(uuid_pkg.uuid4())
    items = []
    for pid in pattern_ids:
        p = pmap.get(pid)
        if not p:
            continue

        # examples (2)
        exs = (await db.execute(
            select(GrammarExample).where(GrammarExample.pattern_id == pid).order_by(GrammarExample.created_at.desc()).limit(2)
        )).scalars().all()

        # exercise (pick latest; you can randomize later)
        ex_stmt = (
            select(GrammarExercise)
            .where(GrammarExercise.pattern_id == pid)
            .order_by(GrammarExercise.created_at.desc())
            .limit(1)
        )
        ex = (await db.execute(ex_stmt)).scalar_one_or_none()

        choices = []
        if ex and ex.exercise_type == GrammarExerciseType.MCQ:
            choices = (await db.execute(
                select(GrammarChoice).where(GrammarChoice.exercise_id == ex.id).order_by(GrammarChoice.sort_order.asc())
            )).scalars().all()

        st = smap.get(pid)
        items.append({
            "pattern": p,
            "examples": exs,
            "exercise": ex,
            "choices": choices,
            "state": {
                "mastery": st.mastery if st else GrammarMastery.NEW,
                "familiarity": int(st.familiarity if st else 0),
                "ease_factor": float(st.ease_factor if st else 2.5),
                "repetition": int(st.repetition if st else 0),
                "interval_days": int(st.interval_days if st else 0),
                "next_review_at": st.next_review_at if st else None,
                "last_reviewed_at": st.last_reviewed_at if st else None,
            }
        })

    return {"session_id": session_id, "items": items, "total": len(items)}


def _evaluate_exercise(ex: GrammarExercise | None, user_answer: dict | None) -> tuple[bool, int, dict]:
    """
    Returns: (is_correct, score_percent, meta)
    Supports:
      - MCQ: user_answer = {"choice_id": "..."}
      - FILL_BLANK/REORDER/ERROR_CORRECTION/TRANSFORM: compare with ex.answer (simple)
    """
    if not ex:
        # no exercise -> treat as reading: give mild positive
        return True, 80, {"mode": "READ_ONLY"}

    ua = user_answer or {}
    meta: dict = {"exercise_type": ex.exercise_type}

    if ex.exercise_type == GrammarExerciseType.MCQ:
        # MCQ: we consider correct if chosen choice is marked correct (need lookup in submit path)
        # This function does not hit DB; caller should pass {"is_correct": True} if it already checked.
        if "is_correct" in ua:
            ok = bool(ua["is_correct"])
            return ok, (100 if ok else 0), meta
        # fallback: if not provided, cannot verify
        return False, 0, {**meta, "error": "MCQ_NO_VERIFICATION"}

    # For other types: naive JSON compare
    expected = ex.answer or {}
    ok = (ua == expected)
    # partial credit optional: if both are strings in "text"
    if not ok and isinstance(ua, dict) and isinstance(expected, dict):
        ut = (ua.get("text") or "").strip()
        et = (expected.get("text") or "").strip()
        if ut and et:
            ok = ut.lower() == et.lower()
    score = 100 if ok else 20
    return ok, score, meta


async def submit_session(db: AsyncSession, user_id: str, language_id: str, session_id: str, items: list[dict]):
    now = datetime.now(timezone.utc)

    updated = []
    for it in items:
        pattern_id = str(it["pattern_id"])
        exercise_id = str(it["exercise_id"]) if it.get("exercise_id") else None
        user_answer = it.get("user_answer") or {}

        # validate pattern belongs to language
        p = (await db.execute(
            select(GrammarPattern).where(GrammarPattern.id == pattern_id, GrammarPattern.language_id == language_id)
        )).scalar_one_or_none()
        if not p:
            continue

        ex = None
        if exercise_id:
            ex = (await db.execute(
                select(GrammarExercise).where(GrammarExercise.id == exercise_id, GrammarExercise.pattern_id == pattern_id)
            )).scalar_one_or_none()

        # MCQ verify: replace choice_id by correctness
        if ex and ex.exercise_type == GrammarExerciseType.MCQ:
            cid = user_answer.get("choice_id")
            if cid:
                ch = (await db.execute(
                    select(GrammarChoice).where(GrammarChoice.id == cid, GrammarChoice.exercise_id == ex.id)
                )).scalar_one_or_none()
                user_answer["is_correct"] = bool(ch.is_correct) if ch else False

        is_correct, score_percent, meta = _evaluate_exercise(ex, user_answer)
        rating = _score_to_rating(int(score_percent))

        # update state (SRS)
        st = await _ensure_state(db, user_id, pattern_id)
        _sm2_update(st, rating)

        # log attempt
        await db.add(GrammarAttempt(
            user_id=user_id,
            language_id=language_id,
            pattern_id=pattern_id,
            exercise_id=exercise_id,
            is_correct=is_correct,
            score_percent=int(score_percent),
            rating=int(rating),
            user_answer=user_answer,
            meta={**meta, "session_id": session_id},
        ))

        updated.append({
            "pattern_id": pattern_id,
            "is_correct": bool(is_correct),
            "score_percent": int(score_percent),
            "rating": int(rating),
            "mastery": st.mastery,
            "familiarity": int(st.familiarity),
            "next_review_at": st.next_review_at,
        })

    await db.commit()
    return updated
