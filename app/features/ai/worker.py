import asyncio
from arq.connections import RedisSettings
from arq import cron
from arq.worker import Retry
from sqlalchemy import select

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.enums import SpeakingTaskType, WordErrorSource
from app.features.ai.service import gemini_score_speaking
from app.features.ai.schemas import AudioInput, SpeakScoreRequest
from app.features.ai.rate_limit import consume_global, consume_user
from app.models.curriculum import Lesson
from app.models.lesson_engine import LessonAttempt
from app.models.speaking_engine import SpeakingAttempt, SpeakingAttemptItem, SpeakingTask
from app.services.lesson_engine_service import enqueue_ai_speaking_job
from app.services.speaking_engine import apply_ai_result, mark_failed
from app.services.vocabulary_service import ingest_speaking_weak_words

# payload format:
# {
#   "attempt_id": "...",
#   "user_id": "...",
#   "items": [
#       {"item_id": "...", "audio_base64": "...", "mime_type": "...", "reference_text": "...", "language_hint": "en"}
#   ],
#   "strictness": 75
# }

async def ai_score_speaking_job(ctx, payload: dict):
    attempt_id = payload["attempt_id"]
    strictness = int(payload.get("strictness") or 70)

    async with AsyncSessionLocal() as db:
        try:
            attempt = await db.get(SpeakingAttempt, attempt_id)
            if not attempt:
                return

            task = await db.get(SpeakingTask, str(attempt.task_id))
            if not task:
                raise ValueError("TASK_NOT_FOUND")

            task_type: SpeakingTaskType = task.task_type

            items = (await db.execute(
                select(SpeakingAttemptItem).where(SpeakingAttemptItem.attempt_id == attempt_id)
            )).scalars().all()

            answers = attempt.answers or {}
            item_scores: dict[str, dict] = {}

            for it in items:
                ans = answers.get(str(it.id)) or {}
                audio_base64 = ans.get("audio_base64")
                mime_type = ans.get("audio_mime") or it.audio_mime or "audio/wav"
                language_hint = ans.get("language_hint")  # optional

                if not audio_base64:
                    raise ValueError("AUDIO_BASE64_REQUIRED")

                # ---- FREE SPEECH: QNA / PICTURE_DESC ----
                if task_type in (SpeakingTaskType.QNA, SpeakingTaskType.PICTURE_DESC):
                    # 1) ASR for transcript + timestamps if needed
                    asr = await gemini_score_speaking(AudioInput(
                        audio_base64=audio_base64,
                        mime_type=mime_type,
                        language_hint=language_hint,
                        diarization=False,
                        timestamps=True,
                    ))

                    transcript = asr.text.strip() if hasattr(asr, "text") else (asr.get("text") or "").strip()
                    if not transcript:
                        transcript = " "  # avoid empty

                    # 2) Use scoring API but pass transcript as reference to satisfy schema
                    score = await gemini_score_speaking(SpeakScoreRequest(
                        audio_base64=audio_base64,
                        mime_type=mime_type,
                        language_hint=language_hint,
                        diarization=False,
                        timestamps=True,
                        reference_text=transcript,   # schema requires; we will ignore accuracy later
                        strictness=strictness,
                        return_word_feedback=True,
                    ))

                    score_dict = score.model_dump() if hasattr(score, "model_dump") else dict(score)
                    # attach ASR detail for UI
                    score_dict["_asr"] = asr.model_dump() if hasattr(asr, "model_dump") else dict(asr)
                    score_dict["_meta"] = {"scoring_mode": "FREE_SPEECH"}

                    item_scores[str(it.id)] = score_dict
                    continue

                # ---- REFERENCE BASED: READ_ALOUD / REPEAT ----
                ref = (it.reference_text or "").strip()
                if not ref:
                    # fallback: if task mistakenly missing reference, still score as free-speech
                    ref = " "

                score = await gemini_score_speaking(SpeakScoreRequest(
                    audio_base64=audio_base64,
                    mime_type=mime_type,
                    language_hint=language_hint,
                    diarization=False,
                    timestamps=True,
                    reference_text=ref,
                    strictness=strictness,
                    return_word_feedback=True,
                ))

                score_dict = score.model_dump() if hasattr(score, "model_dump") else dict(score)
                score_dict["_meta"] = {"scoring_mode": "REFERENCE_BASED"}
                item_scores[str(it.id)] = score_dict

            await apply_ai_result(db, attempt_id=attempt_id, item_scores=item_scores, task_type=task_type)

        except Exception as e:
            await mark_failed(db, attempt_id=attempt_id, err={"error": str(e)})
            raise


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    # Retry policy:
    # - if Gemini fails or rate limit -> raise Retry
    max_jobs = 200
    job_timeout = 60

    # Default retries config
    max_tries = 6

    functions = [ai_score_speaking_job]

    # optional cron cleanup job if you want here
    # cron_jobs = [cron(...)]
