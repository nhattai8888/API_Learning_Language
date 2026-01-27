from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.speaking_engine import SpeakingTask, SpeakingAttempt, SpeakingAttemptItem
from app.core.enums import SpeakingAttemptStatus, SpeakingItemType, SpeakingTaskType
from app.schemas.speaking_engine import SubmitSpeakingAttemptRequest
from app.features.ai.queue import enqueue_ai_speaking_job

from app.services.vocabulary_service import ingest_speaking_weak_words
from app.core.enums import WordErrorSource

def _score_readaloud_like(ai: dict) -> int:
    # Prefer overall if exists
    if ai.get("overall") is not None:
        try:
            return max(0, min(100, int(ai["overall"])))
        except Exception:
            pass
    p = int(ai.get("pronunciation") or 0)
    f = int(ai.get("fluency") or 0)
    a = int(ai.get("accuracy") or 0)
    score = round(0.45 * p + 0.20 * f + 0.35 * a)
    return max(0, min(100, int(score)))


def _score_free_speech(ai: dict) -> int:
    # QNA / Describe: ignore accuracy + ignore overall (overall often assumes reference)
    p = int(ai.get("pronunciation") or 0)
    f = int(ai.get("fluency") or 0)
    score = round(0.65 * p + 0.35 * f)
    return max(0, min(100, int(score)))


def _final_score(task_type: SpeakingTaskType, ai: dict) -> int:
    if task_type in (SpeakingTaskType.QNA, SpeakingTaskType.PICTURE_DESC):
        return _score_free_speech(ai)
    return _score_readaloud_like(ai)


# ---------- Tasks ----------
async def create_task(db: AsyncSession, payload):
    x = SpeakingTask(**payload.model_dump())
    await db.add(x)
    await db.commit()
    await db.refresh(x)
    return x

async def update_task(db: AsyncSession, task_id: str, payload):
    x = await db.get(SpeakingTask, task_id)
    if not x:
        raise ValueError("SPEAKING_TASK_NOT_FOUND")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(x, k, v)
    await db.commit()
    await db.refresh(x)
    return x

async def list_tasks(db: AsyncSession, language_id: str, task_type: str | None = None, limit: int = 50, offset: int = 0):
    stmt = select(SpeakingTask).where(SpeakingTask.language_id == language_id, SpeakingTask.status == "PUBLISHED")
    if task_type:
        stmt = stmt.where(SpeakingTask.task_type == task_type)
    stmt = stmt.order_by(SpeakingTask.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()

async def get_task(db: AsyncSession, task_id: str):
    x = await db.get(SpeakingTask, task_id)
    if not x:
        raise ValueError("SPEAKING_TASK_NOT_FOUND")
    return x


# ---------- Attempt lifecycle ----------
async def start_attempt(db: AsyncSession, user_id: str, language_id: str, task_id: str):
    task = await db.get(SpeakingTask, task_id)
    if not task or str(task.language_id) != str(language_id):
        raise ValueError("TASK_NOT_FOUND")

    attempt = SpeakingAttempt(
        user_id=user_id,
        language_id=language_id,
        task_id=task_id,
        status=SpeakingAttemptStatus.STARTED,
    )
    await db.add(attempt)
    await db.flush()

    item = SpeakingAttemptItem(
        attempt_id=attempt.id,
        item_type=SpeakingItemType.SPEAK,
        prompt_text=task.prompt_text,
        prompt_audio_url=task.prompt_audio_url,
        reference_text=task.reference_text,
        picture_url=task.picture_url,
    )
    await db.add(item)

    await db.commit()
    await db.refresh(attempt)
    await db.refresh(item)

    return attempt, [item]


async def submit_attempt(db: AsyncSession, user_id: str, attempt_id: str, payload: SubmitSpeakingAttemptRequest):
    attempt = await db.get(SpeakingAttempt, attempt_id)
    if not attempt or str(attempt.user_id) != str(user_id):
        raise ValueError("ATTEMPT_NOT_FOUND")

    if attempt.status != SpeakingAttemptStatus.STARTED:
        raise ValueError("ATTEMPT_NOT_ACTIVE")

    items = (await db.execute(
        select(SpeakingAttemptItem).where(SpeakingAttemptItem.attempt_id == attempt_id)
    )).scalars().all()
    item_map = {str(i.id): i for i in items}

    answers = attempt.answers or {}
    need_ai = False

    for it in payload.items:
        item = item_map.get(str(it.item_id))
        if not item:
            continue

        item.audio_url = it.audio_url
        item.audio_mime = it.audio_mime
        item.audio_duration_ms = int(it.duration_ms or 0)

        # ✅ MUST store audio_base64 for worker (Gemini SDK needs bytes)
        answers[str(item.id)] = {
            "audio_url": it.audio_url,
            "media_id": str(it.media_id) if it.media_id else None,   # <— important
            "audio_mime": it.audio_mime,
            "duration_ms": it.duration_ms,
        }

        if it.media_id:
            need_ai = True

    attempt.answers = answers
    attempt.duration_sec = int(payload.duration_sec or 0)
    attempt.submitted_at = datetime.now(timezone.utc)
    attempt.status = SpeakingAttemptStatus.PENDING_AI if need_ai else SpeakingAttemptStatus.SUBMITTED

    await db.commit()
    await db.refresh(attempt)

    if need_ai:
        await enqueue_ai_speaking_job({
            "attempt_id": str(attempt.id),
            "user_id": str(user_id),
            "strictness": int(payload.strictness),
        })

    return attempt


async def get_attempt(db: AsyncSession, user_id: str, attempt_id: str):
    a = await db.get(SpeakingAttempt, attempt_id)
    if not a or str(a.user_id) != str(user_id):
        raise ValueError("ATTEMPT_NOT_FOUND")
    return a


# ---------- Finalize ----------
def _weighted_score(ai: dict) -> int:
    # Prefer "overall" from ScoreResponse; fallback to weighted
    if isinstance(ai, dict) and ai.get("overall") is not None:
        try:
            return max(0, min(100, int(ai["overall"])))
        except Exception:
            pass

    p = int(ai.get("pronunciation") or 0)
    f = int(ai.get("fluency") or 0)
    a = int(ai.get("accuracy") or 0)
    score = round(0.45 * p + 0.20 * f + 0.35 * a)
    return max(0, min(100, int(score)))


async def apply_ai_result(db: AsyncSession, attempt_id: str, item_scores: dict[str, dict], task_type: SpeakingTaskType):
    attempt = await db.get(SpeakingAttempt, attempt_id)
    if not attempt:
        return

    items = (await db.execute(
        select(SpeakingAttemptItem).where(SpeakingAttemptItem.attempt_id == attempt_id)
    )).scalars().all()

    merged = {"items": {}, "summary": {}, "meta": {}}
    all_word_feedback = []

    for it in items:
        ai = item_scores.get(str(it.id))
        if not ai:
            continue
        it.ai_score = ai
        it.is_scored = True
        merged["items"][str(it.id)] = ai
        all_word_feedback.extend(ai.get("word_feedback") or [])

    summary_ai = next(iter(merged["items"].values()), {})

    merged["meta"] = {
        "task_type": str(task_type),
        "scoring_mode": "FREE_SPEECH" if task_type in (SpeakingTaskType.QNA, SpeakingTaskType.PICTURE_DESC) else "REFERENCE_BASED",
    }

    attempt.score_percent = _final_score(task_type, summary_ai)
    attempt.ai_result = {"merged": merged, "summary": summary_ai}
    attempt.status = SpeakingAttemptStatus.SCORED
    attempt.error = None

    await db.commit()

    # Hook weak words → vocab (best-effort)
    try:
        if all_word_feedback:
            await ingest_speaking_weak_words(
                db,
                user_id=str(attempt.user_id),
                language_id=str(attempt.language_id),
                word_feedback=all_word_feedback,
                source=WordErrorSource.SPEAKING,
            )
    except Exception:
        pass



async def mark_failed(db: AsyncSession, attempt_id: str, err: dict):
    attempt = await db.get(SpeakingAttempt, attempt_id)
    if not attempt:
        return
    attempt.status = SpeakingAttemptStatus.FAILED
    attempt.error = err
    await db.commit()
