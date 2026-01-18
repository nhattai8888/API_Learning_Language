from fastapi import APIRouter, Depends, HTTPException
from app.schemas.common import ApiResponse
from app.deps import require_permissions
from app.features.ai.schemas import AudioInput, ASRResponse, SpeakScoreRequest, ScoreResponse
from app.features.ai.service import gemini_asr, gemini_score_speaking

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post(
    "/asr/transcribe",
    dependencies=[Depends(require_permissions(["AI_ASR"]))],
    response_model=ApiResponse[ASRResponse],
)
async def transcribe(payload: AudioInput):
    try:
        data = await gemini_asr(payload)
        return ApiResponse(data=data, message="OK")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ASR_FAILED: {e}")

@router.post(
    "/speaking/score",
    dependencies=[Depends(require_permissions(["AI_SPEAKING_SCORE"]))],
    response_model=ApiResponse[ScoreResponse],
)
async def score(payload: SpeakScoreRequest):
    try:
        data = await gemini_score_speaking(payload)
        return ApiResponse(data=data, message="OK")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SCORE_FAILED: {e}")
