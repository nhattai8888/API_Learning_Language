import asyncio
from arq.connections import RedisSettings
from arq import cron
from arq.worker import Retry

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.features.ai.service import gemini_score_speaking
from app.features.ai.schemas import SpeakScoreRequest
from app.features.ai.rate_limit import consume_global, consume_user
from app.services.lesson_engine_service import apply_ai_result_and_finalize

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
    redis = ctx["redis"]

    user_id = payload["user_id"]
    allowed_g = await consume_global(redis, cost=1)
    allowed_u = await consume_user(redis, user_id=user_id, cost=1)

    if not (allowed_g and allowed_u):
        # Rate limited -> retry later (do not fail)
        raise Retry(defer=5)

    attempt_id = payload["attempt_id"]
    strictness = int(payload.get("strictness", 75))
    items = payload.get("items", [])

    speak_results = {}

    # Call Gemini per SPEAK item (can parallelize lightly; keep modest to avoid quota spikes)
    for it in items:
        req = SpeakScoreRequest(
            audio_base64=it["audio_base64"],
            mime_type=it.get("mime_type", "audio/wav"),
            language_hint=it.get("language_hint"),
            diarization=False,
            timestamps=True,
            reference_text=it["reference_text"],
            strictness=strictness,
            return_word_feedback=True,
        )
        data = await gemini_score_speaking(req)

        # map to lesson-engine ai structure (compatible with /ai-update logic)
        # here we keep only fields used by apply_ai_result_and_finalize policy
        speak_results[it["item_id"]] = {
            "pronunciation": int(data["pronunciation"]),
            "fluency": int(data["fluency"]),
            "accuracy": int(data["accuracy"]),
            "words": data.get("word_feedback") or [],
            "transcript": data.get("transcript"),
            "tips": data.get("tips") or [],
        }

    # Finalize attempt in DB (no HTTP hop)
    async with AsyncSessionLocal() as db:
        await apply_ai_result_and_finalize(
            db,
            attempt_id=attempt_id,
            speak_results=speak_results,
            finalize=True,
        )


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
