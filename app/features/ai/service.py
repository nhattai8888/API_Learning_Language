import base64
from google import genai

from app.core.config import settings
from app.features.ai.prompts import ASR_SYSTEM, ASR_USER, SCORE_SYSTEM, SCORE_USER

def _client() -> genai.Client:
    # SDK tự pick từ env GEMINI_API_KEY, nhưng ta vẫn đảm bảo settings có
    return genai.Client(api_key=settings.GEMINI_API_KEY)

def _audio_part(audio_base64: str, mime_type: str):
    audio_bytes = base64.b64decode(audio_base64)
    return {"inline_data": {"mime_type": mime_type, "data": audio_bytes}}

async def gemini_asr(payload):
    """
    Gemini Audio Understanding: audio -> transcript (+ timestamps/segments nếu prompt yêu cầu)
    """
    client = _client()
    model = settings.GEMINI_ASR_MODEL

    prompt = ASR_USER.format(
        language_hint=payload.language_hint,
        timestamps=payload.timestamps,
        diarization=payload.diarization,
    )

    # Structured outputs JSON schema (Gemini structured output) :contentReference[oaicite:5]{index=5}
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "text": {"type": "STRING"},
            "detected_language": {"type": "STRING"},
            "segments": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "start_ms": {"type": "INTEGER"},
                        "end_ms": {"type": "INTEGER"},
                        "text": {"type": "STRING"},
                        "speaker": {"type": "STRING"}
                    },
                    "required": ["start_ms", "end_ms", "text"]
                }
            },
            "words": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "word": {"type": "STRING"},
                        "start_ms": {"type": "INTEGER"},
                        "end_ms": {"type": "INTEGER"},
                        "confidence": {"type": "NUMBER"},
                        "speaker": {"type": "STRING"}
                    },
                    "required": ["word", "start_ms", "end_ms"]
                }
            }
        },
        "required": ["text"]
    }

    resp = client.models.generate_content(
        model=model,
        contents=[
            {"role": "user", "parts": [
                {"text": ASR_SYSTEM},
                {"text": prompt},
                _audio_part(payload.audio_base64, payload.mime_type),
            ]}
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    return resp.parsed  # SDK parse JSON


async def gemini_score_speaking(payload):
    """
    ELSA-like scoring: audio + reference_text -> scores + word feedback
    """
    client = _client()
    model = settings.GEMINI_SCORE_MODEL

    user_prompt = SCORE_USER.format(
        reference_text=payload.reference_text,
        strictness=payload.strictness,
        return_word_feedback=payload.return_word_feedback,
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "transcript": {"type": "STRING"},
            "pronunciation": {"type": "INTEGER"},
            "fluency": {"type": "INTEGER"},
            "accuracy": {"type": "INTEGER"},
            "overall": {"type": "INTEGER"},
            "wpm": {"type": "INTEGER"},
            "pauses": {"type": "OBJECT"},
            "word_feedback": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "word": {"type": "STRING"},
                        "start_ms": {"type": "INTEGER"},
                        "end_ms": {"type": "INTEGER"},
                        "severity": {"type": "STRING"},
                        "issue": {"type": "STRING"},
                        "suggestion": {"type": "STRING"}
                    },
                    "required": ["word", "start_ms", "end_ms", "severity"]
                }
            },
            "tips": {"type": "ARRAY", "items": {"type": "STRING"}},
            "warnings": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["transcript", "pronunciation", "fluency", "accuracy", "overall", "tips"]
    }

    resp = client.models.generate_content(
        model=model,
        contents=[
            {"role": "user", "parts": [
                {"text": SCORE_SYSTEM},
                {"text": user_prompt},
                _audio_part(payload.audio_base64, payload.mime_type),
            ]}
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    return resp.parsed
