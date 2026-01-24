from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EntityStatus, ReviewMode, WordErrorSource, WordMastery
from app.features.ai.queue import enqueue_ai_speaking_job
from app.features.review.model import ReviewAttempt, UserReviewSettings
from app.models.vocabulary import Lexeme, WordSense, WordExample, UserLexemeState, UserWordError
from app.features.review.srs import sm2_update

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func as sql_func
from app.models.base import Base

import uuid as uuid_pkg



async def get_or_create_settings(db: AsyncSession, user_id: str, language_id: str):
    s = (await db.execute(
        select(UserReviewSettings).where(UserReviewSettings.user_id == user_id, UserReviewSettings.language_id == language_id)
    )).scalar_one_or_none()
    if not s:
        s = UserReviewSettings(user_id=user_id, language_id=language_id, daily_new_limit=10, daily_review_limit=50)
        await db.add(s)
        await db.commit()
        await db.refresh(s)
    return s


async def upsert_settings(db: AsyncSession, user_id: str, language_id: str, daily_new_limit: int, daily_review_limit: int):
    s = (await db.execute(
        select(UserReviewSettings).where(UserReviewSettings.user_id == user_id, UserReviewSettings.language_id == language_id)
    )).scalar_one_or_none()
    if not s:
        s = UserReviewSettings(
            user_id=user_id,
            language_id=language_id,
            daily_new_limit=daily_new_limit,
            daily_review_limit=daily_review_limit,
        )
        await db.add(s)
    else:
        s.daily_new_limit = daily_new_limit
        s.daily_review_limit = daily_review_limit

    await db.commit()
    await db.refresh(s)
    return s


async def _fetch_due_states(db: AsyncSession, user_id: str, language_id: str, limit: int):
    now = datetime.now(timezone.utc)
    stmt = (
        select(UserLexemeState)
        .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
        .where(
            UserLexemeState.user_id == user_id,
            Lexeme.language_id == language_id,
            Lexeme.status == EntityStatus.ACTIVE,
            UserLexemeState.next_review_at.isnot(None),
            UserLexemeState.next_review_at <= now,
        )
        .order_by(UserLexemeState.next_review_at.asc(), UserLexemeState.updated_at.asc())
        .limit(limit)
    )
    return (await db.execute(stmt)).scalars().all()


async def _fetch_new_lexemes(db: AsyncSession, user_id: str, language_id: str, limit: int):
    """
    New = lexemes active in language but NOT in user_lexeme_states.
    Strategy: pick easiest first (difficulty asc) + lemma asc.
    """
    subq = select(UserLexemeState.lexeme_id).where(UserLexemeState.user_id == user_id).subquery()
    stmt = (
        select(Lexeme)
        .where(
            Lexeme.language_id == language_id,
            Lexeme.status == EntityStatus.ACTIVE,
            Lexeme.id.in_(select(subq.c.lexeme_id)),
        )
        .order_by(Lexeme.difficulty.asc(), Lexeme.lemma.asc())
        .limit(limit)
    )
    return (await db.execute(stmt)).scalars().all()


async def _pack_cards(db: AsyncSession, user_id: str, lexeme_ids: list[str]):
    if not lexeme_ids:
        return []

    lexemes = (await db.execute(select(Lexeme).where(Lexeme.id.in_(lexeme_ids)))).scalars().all()
    lex_map = {str(x.id): x for x in lexemes}

    senses = (await db.execute(
        select(WordSense).where(WordSense.lexeme_id.in_(lexeme_ids)).order_by(WordSense.sense_index.asc())
    )).scalars().all()
    sense_map = {}
    for s in senses:
        sense_map.setdefault(str(s.lexeme_id), []).append(s)

    sense_ids = [str(s.id) for s in senses]
    ex_map = {}
    if sense_ids:
        examples = (await db.execute(
            select(WordExample).where(WordExample.sense_id.in_(sense_ids)).order_by(WordExample.created_at.desc())
        )).scalars().all()
        for e in examples:
            ex_map.setdefault(str(e.sense_id), []).append(e)

    states = (await db.execute(
        select(UserLexemeState).where(UserLexemeState.user_id == user_id, UserLexemeState.lexeme_id.in_(lexeme_ids))
    )).scalars().all()
    st_map = {str(s.lexeme_id): s for s in states}

    # weak notes (last few)
    errs = (await db.execute(
        select(UserWordError)
        .where(UserWordError.user_id == user_id, UserWordError.lexeme_id.in_(lexeme_ids))
        .order_by(UserWordError.last_occurred_at.desc())
    )).scalars().all()
    err_map = {}
    for e in errs:
        err_map.setdefault(str(e.lexeme_id), []).append(e)

    cards = []
    for lid in lexeme_ids:
        lx = lex_map.get(lid)
        if not lx:
            continue
        st = st_map.get(lid)

        ss = sense_map.get(lid, [])
        exs = []
        for s in ss[:2]:
            exs.extend((ex_map.get(str(s.id), [])[:1]))

        weak_notes = []
        for e in (err_map.get(lid, [])[:3]):
            weak_notes.append({
                "severity": e.severity,
                "error_type": e.error_type,
                "occur_count": e.occur_count,
                "last_occurred_at": e.last_occurred_at,
                "evidence": e.evidence,
            })

        cards.append({
            "lexeme_id": lx.id,
            "lemma": lx.lemma,
            "type": lx.type,
            "phonetic": lx.phonetic,
            "audio_url": lx.audio_url,
            "difficulty": lx.difficulty,
            "tags": lx.tags,
            "mastery": st.mastery if st else WordMastery.NEW,
            "familiarity": int(st.familiarity) if st else 0,
            "next_review_at": st.next_review_at if st else None,
            "last_reviewed_at": st.last_reviewed_at if st else None,
            "senses": [{
                "id": s.id,
                "sense_index": s.sense_index,
                "definition": s.definition,
                "domain": s.domain,
                "cefr_level": s.cefr_level,
                "translations": s.translations,
                "status": s.status
            } for s in ss],
            "examples": [{
                "id": e.id,
                "sense_id": e.sense_id,
                "sentence": e.sentence,
                "translation": e.translation,
                "audio_url": e.audio_url,
                "difficulty": e.difficulty,
                "tags": e.tags
            } for e in exs],
            "weak_notes": weak_notes or None
        })

    return cards


async def review_today(db: AsyncSession, user_id: str, language_id: str):
    settings = await get_or_create_settings(db, user_id, language_id)

    due_states = await _fetch_due_states(db, user_id, language_id, limit=settings.daily_review_limit)
    due_ids = [str(s.lexeme_id) for s in due_states]

    # fill with new if still room
    remaining = max(0, int(settings.daily_review_limit) - len(due_ids))
    new_lexemes = await _fetch_new_lexemes(db, user_id, language_id, limit=min(int(settings.daily_new_limit), remaining))
    new_ids = [str(x.id) for x in new_lexemes]

    # pre-create states for new words (so UI consistent)
    for lx in new_lexemes:
        st = UserLexemeState(
            user_id=user_id,
            lexeme_id=lx.id,
            mastery=WordMastery.NEW,
            familiarity=0,
            repetition=0,
            interval_days=0,
            lapse_count=0,
            ease_factor=2.5,
            next_review_at=None,
        )
        await db.add(st)

    if new_lexemes:
        await db.commit()

    lexeme_ids = due_ids + new_ids
    cards = await _pack_cards(db, user_id, lexeme_ids)

    return cards, len(cards), len(due_ids), len(new_ids)


async def submit_reviews(db: AsyncSession, user_id: str, language_id: str, items: list[dict]):
    """
    items: [{lexeme_id, rating, source}]
    """
    now = datetime.now(timezone.utc)

    updated = []
    for it in items:
        lexeme_id = str(it["lexeme_id"])
        rating = int(it["rating"])
        source = it.get("source")

        st = (await db.execute(
            select(UserLexemeState)
            .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
            .where(UserLexemeState.user_id == user_id, UserLexemeState.lexeme_id == lexeme_id, Lexeme.language_id == language_id)
        )).scalar_one_or_none()

        if not st:
            # ensure state exists
            st = UserLexemeState(user_id=user_id, lexeme_id=lexeme_id, mastery=WordMastery.NEW, familiarity=0, ease_factor=2.5)
            await db.add(st)
            await db.flush()

        st.last_source = source
        st.updated_at = now
        sm2_update(st, rating)

        updated.append(st)

    await db.commit()
    return updated


async def stats(db: AsyncSession, user_id: str, language_id: str):
    now = datetime.now(timezone.utc)

    due_now = (await db.execute(
        select(func.count(UserLexemeState.id))
        .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
        .where(
            UserLexemeState.user_id == user_id,
            Lexeme.language_id == language_id,
            UserLexemeState.next_review_at.isnot(None),
            UserLexemeState.next_review_at <= now,
        )
    )).scalar_one()

    scheduled_total = (await db.execute(
        select(func.count(UserLexemeState.id))
        .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
        .where(UserLexemeState.user_id == user_id, Lexeme.language_id == language_id)
    )).scalar_one()

    mastered = (await db.execute(
        select(func.count(UserLexemeState.id))
        .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
        .where(UserLexemeState.user_id == user_id, Lexeme.language_id == language_id, UserLexemeState.mastery == WordMastery.MASTERED)
    )).scalar_one()

    learning = (await db.execute(
        select(func.count(UserLexemeState.id))
        .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
        .where(UserLexemeState.user_id == user_id, Lexeme.language_id == language_id, UserLexemeState.mastery.in_([WordMastery.NEW, WordMastery.LEARNING, WordMastery.KNOWN]))
    )).scalar_one()

    avg_fam = (await db.execute(
        select(func.avg(UserLexemeState.familiarity))
        .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
        .where(UserLexemeState.user_id == user_id, Lexeme.language_id == language_id)
    )).scalar_one()
    avg_fam = int(round(float(avg_fam or 0)))

    # reviewed 7d
    seven_days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    reviewed_7d = (await db.execute(
        select(func.count(UserLexemeState.id))
        .join(Lexeme, Lexeme.id == UserLexemeState.lexeme_id)
        .where(UserLexemeState.user_id == user_id, Lexeme.language_id == language_id, UserLexemeState.last_reviewed_at.isnot(None), UserLexemeState.last_reviewed_at >= (datetime.now(timezone.utc) - func.make_interval(days=7)))
    )).scalar_one()

    return {
        "due_now": int(due_now or 0),
        "scheduled_total": int(scheduled_total or 0),
        "mastered": int(mastered or 0),
        "learning": int(learning or 0),
        "avg_familiarity": avg_fam,
        "reviewed_7d": int(reviewed_7d or 0),
    }

def _norm(s: str) -> str:
    return (s or "").strip().lower().replace("’","'")

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()

def score_to_rating(score: int) -> int:
    if score >= 95: return 5
    if score >= 85: return 4
    if score >= 70: return 3
    if score >= 50: return 2
    if score >= 30: return 1
    return 0

async def start_session(db, user_id: str, language_id: str, mode: ReviewMode, limit: int):
    # reuse your review_today selection, but only return ids
    cards, total, due_count, new_count = await review_today(db, user_id=user_id, language_id=language_id)
    # cap by limit
    cards = cards[:limit]
    session_id = str(uuid_pkg.uuid4())

    items = []
    for c in cards:
        prompt = {}
        expected = {}

        # minimal senses/examples included
        senses = c.get("senses", [])
        examples = c.get("examples", [])
        lemma = c["lemma"]

        if mode == ReviewMode.FLASHCARD:
            prompt = {
                "front": lemma,
                "back": senses[:1],
                "examples": examples[:1],
                "audio_url": c.get("audio_url"),
            }
            expected = {"lemma": lemma}
        elif mode == ReviewMode.TYPING:
            prompt = {
                "definition": (senses[:1][0]["definition"] if senses else None),
                "translations": (senses[:1][0].get("translations") if senses else None),
                "audio_url": c.get("audio_url"),
                "hint": {"pos": str(c["type"]), "difficulty": c.get("difficulty", 1)}
            }
            expected = {"lemma": lemma}
        elif mode == ReviewMode.LISTENING:
            prompt = {
                "audio_url": c.get("audio_url"),
                "question": "Type what you hear",
                "definition": (senses[:1][0]["definition"] if senses else None),
            }
            expected = {"lemma": lemma}
        elif mode == ReviewMode.SHADOWING:
            prompt = {
                "shadow_text": lemma,
                "audio_url": c.get("audio_url"),
                "reference_text": lemma,  # later: use example sentence for harder shadowing
            }
            expected = {"reference_text": lemma}

        items.append({
            "lexeme_id": c["lexeme_id"],
            "mode": mode,
            "prompt": prompt,
            "expected": expected
        })

    return {"session_id": session_id, "mode": mode, "items": items, "total": len(items), "due_count": due_count, "new_count": new_count}


async def _ensure_state(db, user_id: str, lexeme_id: str):
    st = (await db.execute(
        select(UserLexemeState).where(UserLexemeState.user_id == user_id, UserLexemeState.lexeme_id == lexeme_id)
    )).scalar_one_or_none()
    if not st:
        st = UserLexemeState(user_id=user_id, lexeme_id=lexeme_id, mastery=WordMastery.NEW, familiarity=0, ease_factor=2.5)
        db.add(st)
        await db.flush()
    return st

async def submit_session(db, user_id: str, language_id: str, session_id: str, items: list[dict]):
    now = datetime.now(timezone.utc)
    updated = []

    # optional: prefetch lexemes to get lemma quickly
    lexeme_ids = [str(x["lexeme_id"]) for x in items]
    lexemes = (await db.execute(select(Lexeme).where(Lexeme.id.in_(lexeme_ids), Lexeme.language_id == language_id))).scalars().all()
    lex_map = {str(l.id): l for l in lexemes}

    for it in items:
        lexeme_id = str(it["lexeme_id"])
        mode = ReviewMode(it["mode"])
        lx = lex_map.get(lexeme_id)
        if not lx:
            continue

        score = 0
        meta = {"mode": mode, "session_id": session_id}

        if mode == ReviewMode.FLASHCARD:
            know = bool(it.get("know"))
            score = 90 if know else 20
            meta["know"] = know

        elif mode == ReviewMode.TYPING:
            ans = it.get("user_answer") or ""
            sim = _similarity(ans, lx.lemma)
            score = 100 if sim >= 0.98 else (85 if sim >= 0.88 else (60 if sim >= 0.70 else 20))
            meta["similarity"] = sim
            meta["user_answer"] = ans
            meta["expected"] = lx.lemma

        elif mode == ReviewMode.LISTENING:
            ans = it.get("user_answer") or ""
            sim = _similarity(ans, lx.lemma)
            score = 100 if sim >= 0.98 else (80 if sim >= 0.85 else (50 if sim >= 0.70 else 10))
            meta["similarity"] = sim
            meta["user_answer"] = ans
            meta["expected"] = lx.lemma

        elif mode == ReviewMode.SHADOWING:
            # ✅ async route: enqueue AI, mark as pending and skip immediate SRS
            audio_base64 = it.get("audio_base64")
            if audio_base64:
                await enqueue_ai_speaking_job({
                    "attempt_id": f"review:{session_id}:{lexeme_id}",
                    "user_id": str(user_id),
                    "language_id": str(language_id),
                    "items": [{
                        "item_id": lexeme_id,
                        "audio_base64": audio_base64,
                        "mime_type": it.get("mime_type") or "audio/wav",
                        "language_hint": None,
                        "reference_text": lx.lemma,
                    }],
                    "strictness": 75,
                    "meta": {"review_session_id": session_id, "review_mode": "SHADOWING"}
                })
                # placeholder result; client can poll /review/shadowing/result
                updated.append({
                    "lexeme_id": lexeme_id,
                    "score_percent": 0,
                    "rating": 0,
                    "is_correct": False,
                    "next_review_at": None,
                    "mastery": WordMastery.LEARNING,
                    "familiarity": 0,
                    "meta": {"pending_ai": True}
                })
                continue
            else:
                score = 0
                meta["error"] = "NO_AUDIO"

        rating = score_to_rating(int(score))
        is_correct = rating >= 3

        # update SRS
        st = await _ensure_state(db, user_id, lexeme_id)
        st.last_source = WordErrorSource.QUIZ
        st.updated_at = now
        sm2_update(st, rating)

        # log review_attempt
        await db.add(ReviewAttempt(
            user_id=user_id,
            language_id=language_id,
            lexeme_id=lexeme_id,
            mode=mode.value,
            is_correct=is_correct,
            score_percent=int(score),
            rating=int(rating),
            user_answer=it.get("user_answer"),
            expected=lx.lemma,
            meta=meta
        ))

        updated.append({
            "lexeme_id": lexeme_id,
            "score_percent": int(score),
            "rating": int(rating),
            "is_correct": bool(is_correct),
            "next_review_at": st.next_review_at,
            "mastery": st.mastery,
            "familiarity": int(st.familiarity),
            "meta": meta
        })

    await db.commit()
    return updated
