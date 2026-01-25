from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.common import ApiResponse
from app.deps import require_permissions, get_current_user_id
from app.services.speaking_engine import *
from app.schemas.speaking_engine import (
    SpeakingTaskCreate, SpeakingTaskUpdate, SpeakingTaskOut,
    StartSpeakingAttemptRequest, StartSpeakingAttemptResponse, SpeakingAttemptItemOut,
    SubmitSpeakingAttemptRequest, SpeakingAttemptOut, SpeakingScoreOut,
)


router = APIRouter(prefix="/speaking", tags=["speaking"])


# --------- Tasks (authoring) ---------
@router.post(
    "/tasks",
    dependencies=[Depends(require_permissions(["SPEAKING_TASK_CREATE"]))],
    response_model=ApiResponse[SpeakingTaskOut]
)
async def create_task(payload: SpeakingTaskCreate, db: AsyncSession = Depends(get_db)):
    try:
        x = await create_task(db, payload)
        return ApiResponse(data=SpeakingTaskOut.model_validate(x, from_attributes=True), message="Created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/tasks/{task_id}",
    dependencies=[Depends(require_permissions(["SPEAKING_TASK_UPDATE"]))],
    response_model=ApiResponse[SpeakingTaskOut]
)
async def update_task(task_id: str, payload: SpeakingTaskUpdate, db: AsyncSession = Depends(get_db)):
    try:
        x = await update_task(db, task_id, payload)
        return ApiResponse(data=SpeakingTaskOut.model_validate(x, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/tasks",
    dependencies=[Depends(require_permissions(["SPEAKING_TASK_READ"]))],
    response_model=ApiResponse[list[SpeakingTaskOut]]
)
async def list_tasks(language_id: str, task_type: str | None = None, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    try:
        rows = await list_tasks(db, language_id=language_id, task_type=task_type, limit=limit, offset=offset)
        return ApiResponse(data=[SpeakingTaskOut.model_validate(r, from_attributes=True) for r in rows])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/tasks/{task_id}",
    dependencies=[Depends(require_permissions(["SPEAKING_TASK_READ"]))],
    response_model=ApiResponse[SpeakingTaskOut]
)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    try:
        x = await get_task(db, task_id)
        return ApiResponse(data=SpeakingTaskOut.model_validate(x, from_attributes=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# --------- Attempt flow (student) ---------
@router.post(
    "/attempts/start",
    dependencies=[Depends(require_permissions(["SPEAKING_ATTEMPT"]))],
    response_model=ApiResponse[StartSpeakingAttemptResponse]
)
async def start_attempt(payload: StartSpeakingAttemptRequest, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        attempt, items = await start_attempt(db, user_id=str(user_id), language_id=str(payload.language_id), task_id=str(payload.task_id))
        return ApiResponse(data=StartSpeakingAttemptResponse(
            attempt_id=attempt.id,
            task_id=attempt.task_id,
            status=attempt.status,
            items=[SpeakingAttemptItemOut(id=i.id, prompt_text=i.prompt_text, prompt_audio_url=i.prompt_audio_url, reference_text=i.reference_text, picture_url=i.picture_url) for i in items]
        ))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/attempts/{attempt_id}/submit",
    dependencies=[Depends(require_permissions(["SPEAKING_ATTEMPT"]))],
    response_model=ApiResponse[SpeakingScoreOut]
)
async def submit_attempt(attempt_id: str, payload: SubmitSpeakingAttemptRequest, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        a = await submit_attempt(db, user_id=str(user_id), attempt_id=attempt_id, payload=payload)
        return ApiResponse(data=SpeakingScoreOut(
            attempt_id=a.id,
            status=a.status,
            score_percent=a.score_percent,
            ai_result=a.ai_result,
            error=a.error,
        ), message="Submitted")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/attempts/{attempt_id}",
    dependencies=[Depends(require_permissions(["SPEAKING_ATTEMPT"]))],
    response_model=ApiResponse[SpeakingAttemptOut]
)
async def get_attempt(attempt_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        a = await get_attempt(db, user_id=str(user_id), attempt_id=attempt_id)
        return ApiResponse(data=SpeakingAttemptOut.model_validate(a, from_attributes=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/attempts/{attempt_id}/score",
    dependencies=[Depends(require_permissions(["SPEAKING_ATTEMPT"]))],
    response_model=ApiResponse[SpeakingScoreOut]
)
async def get_score(attempt_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        a = await get_attempt(db, user_id=str(user_id), attempt_id=attempt_id)
        return ApiResponse(data=SpeakingScoreOut(
            attempt_id=a.id,
            status=a.status,
            score_percent=a.score_percent,
            ai_result=a.ai_result,
            error=a.error,
        ))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
