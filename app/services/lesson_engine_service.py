from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from app.features.ai.queue import enqueue_ai_speaking_job
from app.models.lesson_engine import LessonItem, LessonItemChoice, LessonAttempt, UserLessonProgress
from app.core.enums import EntityStatus, LessonItemType, LessonProgressStatus, AttemptStatus


# ---------------- Items ----------------
async def create_item(db: AsyncSession, payload):
    try:
        item = LessonItem(
            lesson_id=str(payload.lesson_id),
            item_type=payload.item_type,
            prompt=payload.prompt,
            content=payload.content,
            correct_answer=payload.correct_answer,
            points=payload.points,
            sort_order=payload.sort_order,
            status=EntityStatus.ACTIVE,
        )
        await db.add(item)
        await db.flush()

        choices_out = []
        if payload.choices:
            for c in payload.choices:
                await db.add(LessonItemChoice(
                    item_id=item.id,
                    key=c.key,
                    text=c.text,
                    is_correct=c.is_correct,
                    sort_order=c.sort_order,
                ))

        await db.commit()
        await db.refresh(item)
        return item
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("ITEM_CREATION_FAILED_INTEGRITY") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"ITEM_CREATION_FAILED: {str(e)}") from e

async def update_item(db: AsyncSession, item_id: str, payload):
    try:
        item = await db.get(LessonItem, item_id)
        if not item:
            raise ValueError("ITEM_NOT_FOUND")

        if payload.prompt is not None:
            item.prompt = payload.prompt
        if payload.content is not None:
            item.content = payload.content
        if payload.correct_answer is not None:
            item.correct_answer = payload.correct_answer
        if payload.points is not None:
            item.points = payload.points
        if payload.sort_order is not None:
            item.sort_order = payload.sort_order
        if payload.status is not None:
            # accept only ACTIVE/DISABLED
            item.status = EntityStatus(payload.status)

        # replace choices if provided
        if payload.choices is not None:
            await db.execute(delete(LessonItemChoice).where(LessonItemChoice.item_id == item.id))
            for c in payload.choices:
                await db.add(LessonItemChoice(
                    item_id=item.id,
                    key=c.key,
                    text=c.text,
                    is_correct=c.is_correct,
                    sort_order=c.sort_order,
                ))

        await db.commit()
        await db.refresh(item)
        return item
    except ValueError:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("ITEM_UPDATE_FAILED_INTEGRITY") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"ITEM_UPDATE_FAILED: {str(e)}") from e

async def list_items_by_lesson(db: AsyncSession, lesson_id: str):
    try:
        items = (await db.execute(
            select(LessonItem).where(LessonItem.lesson_id == lesson_id).order_by(LessonItem.sort_order)
        )).scalars().all()
        return items
    except Exception as e:
        raise ValueError(f"LIST_ITEMS_FAILED: {str(e)}") from e

async def list_choices_for_items(db: AsyncSession, item_ids: list[str]):
    try:
        if not item_ids:
            return {}
        rows = (await db.execute(
            select(LessonItemChoice).where(LessonItemChoice.item_id.in_(item_ids)).order_by(LessonItemChoice.sort_order)
        )).scalars().all()
        mp = {}
        for r in rows:
            mp.setdefault(str(r.item_id), []).append(r)
        return mp
    except Exception as e:
        raise ValueError(f"LIST_CHOICES_FAILED: {str(e)}") from e


# ---------------- Attempts ----------------
async def start_attempt(db: AsyncSession, user_id: str, lesson_id: str):
    try:
        # load items
        items = await list_items_by_lesson(db, lesson_id)
        item_ids = [str(i.id) for i in items]
        choices_map = await list_choices_for_items(db, item_ids)

        attempt = LessonAttempt(
            user_id=user_id,
            lesson_id=lesson_id,
            status=AttemptStatus.STARTED,
            max_points=sum([i.points for i in items]),
            score_points=0,
            score_percent=0,
        )
        await db.add(attempt)
        await db.commit()
        await db.refresh(attempt)

        return attempt, items, choices_map
    except Exception as e:
        await db.rollback()
        raise ValueError(f"START_ATTEMPT_FAILED: {str(e)}") from e

def _norm_text(x: str) -> str:
    try:
        return " ".join((x or "").strip().lower().split())
    except Exception as e:
        raise ValueError(f"NORM_TEXT_FAILED: {str(e)}") from e

def _score_item(item: LessonItem, choices: list[LessonItemChoice] | None, ans: dict | None):
    """
    Returns: (is_correct, earned_points, detail)
    """
    try:
        max_points = item.points
        if ans is None:
            return False, 0, {"reason": "NO_ANSWER"}

        answer = ans.get("answer")
        detail = {}

        # MCQ / LISTEN: answer = choice key
        if item.item_type in (LessonItemType.MCQ, LessonItemType.LISTEN):
            if not choices:
                return False, 0, {"reason": "NO_CHOICES"}
            correct_keys = {c.key for c in choices if c.is_correct}
            is_correct = str(answer) in correct_keys
            detail = {"selected": answer, "correct_keys": list(correct_keys)}
            return is_correct, (max_points if is_correct else 0), detail

        # CLOZE: answer = string; correct_answer = {"text": "..."} or {"answers":[...]}
        if item.item_type == LessonItemType.CLOZE:
            ca = (item.correct_answer or {})
            expected_list = ca.get("answers") or ([ca.get("text")] if ca.get("text") else [])
            expected_list = [_norm_text(x) for x in expected_list if x is not None]
            is_correct = _norm_text(str(answer)) in set(expected_list)
            detail = {"expected": expected_list, "got": _norm_text(str(answer))}
            return is_correct, (max_points if is_correct else 0), detail

        # REORDER: answer = ["w1","w2",...]; correct_answer={"sequence":[...]}
        if item.item_type == LessonItemType.REORDER:
            ca = (item.correct_answer or {})
            expected = ca.get("sequence") or []
            is_correct = list(answer or []) == expected
            detail = {"expected": expected, "got": answer}
            return is_correct, (max_points if is_correct else 0), detail

        # MATCH: answer = [{"left":"a","right":"1"},...]; correct_answer={"pairs":[...]}
        if item.item_type == LessonItemType.MATCH:
            ca = (item.correct_answer or {})
            expected = ca.get("pairs") or []
            is_correct = (answer == expected)
            detail = {"expected": expected, "got": answer}
            return is_correct, (max_points if is_correct else 0), detail

        # SPEAK: do not auto score here -> pending AI
        if item.item_type == LessonItemType.SPEAK:
            return False, 0, {"reason": "PENDING_AI"}

        return False, 0, {"reason": "UNSUPPORTED_TYPE"}
    except Exception as e:
        raise ValueError(f"SCORE_ITEM_FAILED: {str(e)}") from e


async def submit_attempt(db: AsyncSession, user_id: str, lesson_id: str, attempt_id: str, answers: dict, duration_sec: int):
    try:
        attempt = await db.get(LessonAttempt, attempt_id)
        if not attempt or str(attempt.user_id) != str(user_id) or str(attempt.lesson_id) != str(lesson_id):
            raise ValueError("ATTEMPT_NOT_FOUND")

        if attempt.status != AttemptStatus.STARTED:
            raise ValueError("ATTEMPT_NOT_ACTIVE")

        items = await list_items_by_lesson(db, lesson_id)
        item_ids = [str(i.id) for i in items]
        choices_map = await list_choices_for_items(db, item_ids)

        total = 0
        max_points = sum([i.points for i in items])
        results = []
        need_ai = False

        for item in items:
            item_ans = answers.get(str(item.id))
            is_correct, earned, detail = _score_item(item, choices_map.get(str(item.id)), item_ans)
            if item.item_type == LessonItemType.SPEAK:
                need_ai = True
            total += earned
            results.append({
                "item_id": str(item.id),
                "is_correct": bool(is_correct),
                "earned_points": int(earned),
                "max_points": int(item.points),
                "detail": detail,
            })

        percent = int(round((total / max_points) * 100)) if max_points > 0 else 0
        attempt.status = AttemptStatus.PENDING_AI 
        if need_ai:
            try:
                # Build job payload with audio + reference per speak item
                speak_items = [i for i in items if i.item_type == LessonItemType.SPEAK]

                job_items = []
                for item in speak_items:
                    item_ans = answers.get(str(item.id)) or {}
                    meta = (item_ans.get("meta") or {})

                    # audio should come from client in meta
                    audio_base64 = meta.get("audio_base64")
                    mime_type = meta.get("mime_type", "audio/wav")
                    language_hint = meta.get("language_hint")

                    # reference_text should be stored in item.content
                    ref = (item.content or {}).get("reference_text") or (item.correct_answer or {}).get("reference_text")
                    if not ref:
                        ref = ""  # or raise if you require

                    if audio_base64:
                        job_items.append({
                            "item_id": str(item.id),
                            "audio_base64": audio_base64,
                            "mime_type": mime_type,
                            "language_hint": language_hint,
                            "reference_text": ref,
                        })

                await enqueue_ai_speaking_job({
                    "attempt_id": str(attempt.id),
                    "user_id": str(user_id),
                    "items": job_items,
                    "strictness": 75,
                })
            except Exception as ai_error:
                # Log AI job error but don't fail the attempt
                raise ValueError(f"AI_JOB_ENQUEUE_FAILED: {str(ai_error)}") from ai_error

        attempt.submitted_at = datetime.now(timezone.utc)
        attempt.duration_sec = int(duration_sec or 0)
        attempt.score_points = int(total)
        attempt.max_points = int(max_points)
        attempt.score_percent = int(percent)
        attempt.answers = answers
        attempt.result_breakdown = {"results": results}

        # Upsert progress
        prog = (await db.execute(
            select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.lesson_id == lesson_id)
        )).scalar_one_or_none()

        if not prog:
            prog = UserLessonProgress(user_id=user_id, lesson_id=lesson_id)
            await db.add(prog)
            await db.flush()

        prog.attempts += 1
        prog.status = LessonProgressStatus.COMPLETED if attempt.status != AttemptStatus.PENDING_AI else LessonProgressStatus.IN_PROGRESS
        prog.best_score = max(int(prog.best_score or 0), percent)

        await db.commit()
        await db.refresh(attempt)
        return attempt, results
    except ValueError:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("SUBMIT_ATTEMPT_FAILED_INTEGRITY") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"SUBMIT_ATTEMPT_FAILED: {str(e)}") from e
