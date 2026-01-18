from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AudioInput(BaseModel):
    # base64 audio bytes
    audio_base64: str
    mime_type: str = Field(default="audio/wav")  # audio/wav, audio/mpeg...
    language_hint: Optional[str] = None          # "en", "vi", "zh"...
    diarization: bool = False
    timestamps: bool = True

class TranscriptWord(BaseModel):
    word: str
    start_ms: int
    end_ms: int
    confidence: Optional[float] = None
    speaker: Optional[str] = None

class TranscriptSegment(BaseModel):
    start_ms: int
    end_ms: int
    text: str
    speaker: Optional[str] = None

class ASRResponse(BaseModel):
    text: str
    words: Optional[List[TranscriptWord]] = None
    segments: Optional[List[TranscriptSegment]] = None
    detected_language: Optional[str] = None


# ----- ELSA-like Scoring -----
class SpeakScoreRequest(AudioInput):
    reference_text: str = Field(min_length=1)
    strictness: int = Field(default=70, ge=0, le=100) 
    return_word_feedback: bool = True

class WordFeedback(BaseModel):
    word: str
    start_ms: int
    end_ms: int
    severity: str  # "good" | "ok" | "bad"
    issue: Optional[str] = None
    suggestion: Optional[str] = None

class ScoreResponse(BaseModel):
    transcript: str
    pronunciation: int = Field(ge=0, le=100)
    fluency: int = Field(ge=0, le=100)
    accuracy: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)
    wpm: Optional[int] = None
    pauses: Optional[Dict[str, Any]] = None
    word_feedback: Optional[List[WordFeedback]] = None
    tips: List[str] = []
    warnings: Optional[List[str]] = None
