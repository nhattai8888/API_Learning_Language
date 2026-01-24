from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.enums import ReviewMode
from app.schemas.common import ApiResponse
from app.deps import require_permissions, get_current_user_id
from app.features.review.schemas import (
    ReviewSessionResponse, ReviewSessionSubmitRequest, ReviewSessionSubmitResponse, ReviewTodayResponse, ReviewSubmitRequest, ReviewSubmitResponse,
    ReviewSubmitResultItem, ReviewStatsResponse,
    ReviewSettingsUpsert, ReviewSettingsOut
)
from app.features.review import service as review_service

router = APIRouter(prefix="/review", tags=["review"])


@router.get(
    "/today",
    dependencies=[Depends(require_permissions(["SRS_REVIEW"]))],
    response_model=ApiResponse[ReviewTodayResponse],
)
async def today(language_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    cards, total, due_count, new_count = await review_service.review_today(db, user_id=user_id, language_id=language_id)
    return ApiResponse(data=ReviewTodayResponse(items=cards, total=total, due_count=due_count, new_count=new_count))


@router.post(
    "/submit",
    dependencies=[Depends(require_permissions(["SRS_REVIEW"]))],
    response_model=ApiResponse[ReviewSubmitResponse],
)
async def submit(payload: ReviewSubmitRequest, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        updated = await review_service.submit_reviews(
            db,
            user_id=user_id,
            language_id=str(payload.language_id),
            items=[x.model_dump() for x in payload.items],
        )
        out = []
        for st in updated:
            out.append(ReviewSubmitResultItem(
                lexeme_id=st.lexeme_id,
                mastery=st.mastery,
                familiarity=st.familiarity,
                ease_factor=float(st.ease_factor),
                repetition=st.repetition,
                interval_days=st.interval_days,
                next_review_at=st.next_review_at,
            ))
        return ApiResponse(data=ReviewSubmitResponse(updated=out, count=len(out)), message="OK")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"REVIEW_SUBMIT_FAILED: {e}")


@router.get(
    "/stats",
    dependencies=[Depends(require_permissions(["SRS_STATS"]))],
    response_model=ApiResponse[ReviewStatsResponse],
)
async def stats(language_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    s = await review_service.stats(db, user_id=user_id, language_id=language_id)
    return ApiResponse(data=ReviewStatsResponse(language_id=language_id, **s))


@router.get(
    "/settings",
    dependencies=[Depends(require_permissions(["SRS_SETTINGS"]))],
    response_model=ApiResponse[ReviewSettingsOut],
)
async def get_settings(language_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    s = await review_service.get_or_create_settings(db, user_id=user_id, language_id=language_id)
    return ApiResponse(data=ReviewSettingsOut(language_id=s.language_id, daily_new_limit=s.daily_new_limit, daily_review_limit=s.daily_review_limit))


@router.post(
    "/settings",
    dependencies=[Depends(require_permissions(["SRS_SETTINGS"]))],
    response_model=ApiResponse[ReviewSettingsOut],
)
async def upsert_settings(payload: ReviewSettingsUpsert, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    s = await review_service.upsert_settings(
        db,
        user_id=user_id,
        language_id=str(payload.language_id),
        daily_new_limit=payload.daily_new_limit,
        daily_review_limit=payload.daily_review_limit,
    )
    return ApiResponse(data=ReviewSettingsOut(language_id=s.language_id, daily_new_limit=s.daily_new_limit, daily_review_limit=s.daily_review_limit), message="Updated")

@router.get(
  "/session",
  dependencies=[Depends(require_permissions(["SRS_REVIEW"]))],
  response_model=ApiResponse[ReviewSessionResponse],
)
async def start_session(language_id: str, mode: ReviewMode, limit: int = 20, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    data = await review_service.start_session(db, user_id=user_id, language_id=language_id, mode=mode, limit=limit)
    return ApiResponse(data=data)

@router.post(
  "/session/submit",
  dependencies=[Depends(require_permissions(["SRS_REVIEW"]))],
  response_model=ApiResponse[ReviewSessionSubmitResponse],
)
async def submit_session(payload: ReviewSessionSubmitRequest, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    updated = await review_service.submit_session(
        db,
        user_id=user_id,
        language_id=str(payload.language_id),
        session_id=payload.session_id,
        items=[x.model_dump() for x in payload.items],
    )
    return ApiResponse(data={"updated": updated, "count": len(updated)}, message="OK")