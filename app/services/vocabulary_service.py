import re
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import IntegrityError

from app.core.enums import EntityStatus, WordMastery, WordErrorSource, WordErrorType, Severity
from app.models.vocabulary import Lexeme, WordSense, WordExample, LessonLexeme, UserLexemeState, UserWordError

_WORD_CLEAN_RE = re.compile(r"[^a-zA-ZÀ-ỹ0-9'’-]+")
# ---------- Lexeme CRUD ----------
async def create_lexeme(db: AsyncSession, payload):
    lex = Lexeme(
        language_id=payload.language_id,
        type=payload.type,
        lemma=payload.lemma,
        phoenic=payload.phoenic,
        audio_url=payload.audio_url,
        difficulty=payload.difficulty,
        tags=payload.tags,
        status=EntityStatus.ACTIVE,
    )
    await db.add(lex)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("LEXEME_EXISTS")
    await db.refresh(lex)
    return lex

async def update_lexeme(db: AsyncSession, lexeme_id: str, payload):
    lex = await db.get(Lexeme, lexeme_id)
    if not lex:
        raise ValueError("LEXEME_NOT_FOUND")

    for f in ("type","lemma","phoenic","audio_url","difficulty","tags","status"):
        v = getattr(payload, f, None)
        if v is not None:
            setattr(lex, f, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("LEXEME_UPDATE_CONFLICT")

    await db.refresh(lex)
    return lex

async def get_lexeme(db: AsyncSession, lexeme_id: str):
    lex = await db.get(Lexeme, lexeme_id)
    if not lex:
        raise ValueError("LEXEME_NOT_FOUND")
    return lex

async def list_lexemes(db: AsyncSession, language_id: str, q: str | None = None, limit: int = 50, offset: int = 0):
    stmt = select(Lexeme).where(Lexeme.language_id == language_id)

    if q:
        # simple ilike; if you have trgm index, use it on lower(lemma) side in SQL
        stmt = stmt.where(Lexeme.lemma.ilike(f"%{q}%"))

    stmt = stmt.order_by(Lexeme.lemma.asc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


# ---------- Sense CRUD ----------
async def create_sense(db: AsyncSession, payload):
    s = WordSense(**payload.model_dump())
    await db.add(s)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("SENSE_EXISTS")
    await db.refresh(s)
    return s

async def update_sense(db: AsyncSession, sense_id: str, payload):
    s = await db.get(WordSense, sense_id)
    if not s:
        raise ValueError("SENSE_NOT_FOUND")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(s, k, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("SENSE_UPDATE_CONFLICT")

    await db.refresh(s)
    return s

async def list_senses_by_lexeme(db: AsyncSession, lexeme_id: str):
    stmt = select(WordSense).where(WordSense.lexeme_id == lexeme_id).order_by(WordSense.sense_index.asc())
    return (await db.execute(stmt)).scalars().all()


# ---------- Example CRUD ----------
async def create_example(db: AsyncSession, payload):
    ex = WordExample(**payload.model_dump())
    await db.add(ex)
    await db.commit()
    await db.refresh(ex)
    return ex

async def update_example(db: AsyncSession, example_id: str, payload):
    ex = await db.get(WordExample, example_id)
    if not ex:
        raise ValueError("EXAMPLE_NOT_FOUND")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(ex, k, v)
    await db.commit()
    await db.refresh(ex)
    return ex

async def list_examples_by_sense(db: AsyncSession, sense_id: str, limit: int = 20):
    stmt = select(WordExample).where(WordExample.sense_id == sense_id).order_by(WordExample.created_at.desc()).limit(limit)
    return (await db.execute(stmt)).scalars().all()


# ---------- Attach vocab to lesson ----------
async def attach_lexemes_to_lesson(db: AsyncSession, lesson_id: str, lexemes: list[dict]):
    # replace all
    await db.execute(delete(LessonLexeme).where(LessonLexeme.lesson_id == lesson_id))

    for it in lexemes:
        await db.add(LessonLexeme(
            lesson_id=lesson_id,
            lexeme_id=it["lexeme_id"],
            is_core=bool(it.get("is_core", True)),
            sort_order=int(it.get("sort_order", 0)),
        ))
    await db.commit()

    stmt = select(LessonLexeme).where(LessonLexeme.lesson_id == lesson_id).order_by(LessonLexeme.sort_order.asc())
    return (await db.execute(stmt)).scalars().all()

async def list_lesson_lexemes(db: AsyncSession, lesson_id: str):
    stmt = select(LessonLexeme).where(LessonLexeme.lesson_id == lesson_id).order_by(LessonLexeme.sort_order.asc())
    return (await db.execute(stmt)).scalars().all()


# ---------- SRS (SM-2 lite) ----------
def _sm2_update(state: UserLexemeState, rating: int):
    """
    rating: 0..5 (0 fail, 5 perfect)
    - updates ease_factor, repetition, interval_days, next_review_at
    """
    now = datetime.now(timezone.utc)

    ef = float(state.ease_factor or 2.5)
    rep = int(state.repetition or 0)
    interval = int(state.interval_days or 0)

    if rating < 3:
        rep = 0
        interval = 1
        state.lapse_count = int(state.lapse_count or 0) + 1
        state.mastery = WordMastery.LEARNING
        state.familiarity = max(0, int(state.familiarity or 0) - 8)
    else:
        rep += 1
        if rep == 1:
            interval = 1
        elif rep == 2:
            interval = 3
        else:
            interval = max(1, int(round(interval * ef)))

        # EF update (SM-2)
        ef = ef + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        ef = min(2.8, max(1.3, ef))

        state.familiarity = min(100, int(state.familiarity or 0) + (6 + rating))
        if state.familiarity >= 85:
            state.mastery = WordMastery.MASTERED
        elif state.familiarity >= 60:
            state.mastery = WordMastery.KNOWN
        else:
            state.mastery = WordMastery.LEARNING

    state.ease_factor = ef
    state.repetition = rep
    state.interval_days = interval
    state.last_reviewed_at = now
    state.next_review_at = now + timedelta(days=interval)


async def review_today(db: AsyncSession, user_id: str, language_id: str, limit: int = 20):
    now = datetime.now(timezone.utc)

    # due cards
    stmt = (
        select(UserLexemeState)
        .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
        .where(
            UserLexemeState.user_id == user_id,
            Lexeme.language_id == language_id,
            Lexeme.status == EntityStatus.ACTIVE,
            (UserLexemeState.next_review_at.is_(None)) | (UserLexemeState.next_review_at <= now),
        )
        .order_by(UserLexemeState.next_review_at.asc().nullsfirst(), UserLexemeState.updated_at.asc())
        .limit(limit)
    )
    states = (await db.execute(stmt)).scalars().all()
    lexeme_ids = [str(s.lexeme_id) for s in states]

    if not lexeme_ids:
        return [], 0

    lexemes = (await db.execute(select(Lexeme).where(Lexeme.id.in_(lexeme_ids)))).scalars().all()
    lex_map = {str(x.id): x for x in lexemes}

    senses = (await db.execute(select(WordSense).where(WordSense.lexeme_id.in_(lexeme_ids)).order_by(WordSense.sense_index.asc()))).scalars().all()
    sense_map = {}
    for s in senses:
        sense_map.setdefault(str(s.lexeme_id), []).append(s)

    # examples: take up to 2 per lexeme (simple strategy)
    sense_ids = [str(s.id) for s in senses]
    ex_map_by_sense = {}
    if sense_ids:
        examples = (await db.execute(
            select(WordExample).where(WordExample.sense_id.in_(sense_ids)).order_by(WordExample.created_at.desc())
        )).scalars().all()
        for e in examples:
            ex_map_by_sense.setdefault(str(e.sense_id), []).append(e)

    cards = []
    for st in states:
        lx = lex_map.get(str(st.lexeme_id))
        ss = sense_map.get(str(st.lexeme_id), [])
        exs = []
        for s in ss[:2]:
            exs.extend((ex_map_by_sense.get(str(s.id), [])[:1]))
        cards.append((lx, ss, exs, st))

    return cards, len(cards)


async def review_result(db: AsyncSession, user_id: str, lexeme_id: str, rating: int, source: WordErrorSource):
    now = datetime.now(timezone.utc)

    st = (await db.execute(
        select(UserLexemeState).where(UserLexemeState.user_id == user_id, UserLexemeState.lexeme_id == lexeme_id)
    )).scalar_one_or_none()

    if not st:
        st = UserLexemeState(user_id=user_id, lexeme_id=lexeme_id, mastery=WordMastery.NEW, familiarity=0)
        await db.add(st)
        await db.flush()

    st.last_source = source
    _sm2_update(st, rating)

    st.updated_at = now
    await db.commit()
    await db.refresh(st)
    return st


# ---------- Weak words (from AI) ----------
async def list_weak_words(db: AsyncSession, user_id: str, language_id: str, limit: int = 50):
    # join lexemes to filter by language
    stmt = (
        select(UserWordError, Lexeme)
        .join(Lexeme, Lexeme.id == UserWordError.lexeme_id)
        .where(UserWordError.user_id == user_id, Lexeme.language_id == language_id)
        .order_by(UserWordError.last_occurred_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return rows


async def upsert_word_error(
    db: AsyncSession,
    user_id: str,
    lexeme_id: str,
    error_type: WordErrorType,
    source: WordErrorSource,
    severity: Severity,
    evidence: dict | None = None
):
    """
    Use when AI detects weak word.
    Strategy: if record exists -> increment occur_count + update last_occurred + evidence
    """
    row = (await db.execute(
        select(UserWordError).where(UserWordError.user_id == user_id, UserWordError.lexeme_id == lexeme_id, UserWordError.error_type == error_type)
    )).scalar_one_or_none()

    if row:
        row.occur_count += 1
        row.last_occurred_at = datetime.now(timezone.utc)
        row.source = source
        row.severity = severity
        row.evidence = evidence
    else:
        await db.add(UserWordError(
            user_id=user_id,
            lexeme_id=lexeme_id,
            error_type=error_type,
            source=source,
            severity=severity,
            evidence=evidence,
        ))

    await db.commit()

def _norm_word(w: str) -> str:
    w = (w or "").strip().lower()
    w = _WORD_CLEAN_RE.sub("", w)
    # normalize fancy apostrophes
    w = w.replace("’", "'").replace("–", "-").replace("—", "-")
    return w

def _map_severity(s: str | None) -> Severity:
    s = (s or "").upper()
    if s == "BAD":
        return Severity.BAD
    if s == "GOOD":
        return Severity.GOOD
    return Severity.OK

async def _find_lexeme_by_word(db: AsyncSession, language_id: str, word: str) -> Lexeme | None:
    """
    Find lexeme by lemma exact match (normalized). Fast path.
    You can extend later to support forms, synonyms.
    """
    w = _norm_word(word)
    if not w:
        return None

    stmt = select(Lexeme).where(
        Lexeme.language_id == language_id,
        Lexeme.lemma.ilike(w)  # exact-ish; if you store lower(lemma) index, use func.lower compare
    ).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none()

async def ingest_speaking_weak_words(
    db: AsyncSession,
    user_id: str,
    language_id: str,
    word_feedback: list[dict],
    source: WordErrorSource = WordErrorSource.SPEAKING
) -> dict:
    """
    Input: Gemini word_feedback list (each has word,start_ms,end_ms,severity,issue,suggestion)
    Action:
    - map word -> lexeme
    - upsert user_word_errors
    - update user_lexeme_states: decrease familiarity + schedule early review
    """
    now = datetime.now(timezone.utc)
    matched = 0
    skipped = 0

    for wf in (word_feedback or []):
        raw_word = wf.get("word") or ""
        sev = _map_severity(wf.get("severity"))
        if sev in (Severity.GOOD, Severity.OK):
            # only treat BAD as weak word (you can widen to OK later)
            continue

        lex = await _find_lexeme_by_word(db, language_id, raw_word)
        if not lex:
            skipped += 1
            continue

        matched += 1
        evidence = {
            "word": raw_word,
            "start_ms": wf.get("start_ms"),
            "end_ms": wf.get("end_ms"),
            "issue": wf.get("issue"),
            "suggestion": wf.get("suggestion"),
        }

        # 1) upsert error log
        await upsert_word_error(
            db,
            user_id=user_id,
            lexeme_id=str(lex.id),
            error_type=WordErrorType.PRONUNCIATION,  # speaking default
            source=source,
            severity=sev,
            evidence=evidence,
        )

        # 2) push into SRS (decrease familiarity & schedule early)
        st = (await db.execute(
            select(UserLexemeState).where(
                UserLexemeState.user_id == user_id,
                UserLexemeState.lexeme_id == lex.id
            )
        )).scalar_one_or_none()

        if not st:
            st = UserLexemeState(user_id=user_id, lexeme_id=lex.id, mastery=WordMastery.LEARNING, familiarity=0)
            db.add(st)
            await db.flush()

        # penalty
        st.familiarity = max(0, int(st.familiarity or 0) - 10)
        st.mastery = WordMastery.LEARNING
        st.last_source = source
        st.updated_at = now

        # schedule soon (force review)
        # if already due sooner, keep earliest
        next_at = now + timedelta(hours=12)
        if not st.next_review_at or st.next_review_at > next_at:
            st.next_review_at = next_at

    await db.commit()
    return {"matched": matched, "skipped": skipped}