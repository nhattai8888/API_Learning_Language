from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.common import ApiResponse
from app.deps import require_permissions, get_current_user_id

from app.schemas.lesson_engine import (
    LessonItemCreate, LessonItemUpdate, LessonItemOut,
    ChoiceOut,
    AttemptStartResponse, AttemptSubmitRequest, AttemptSubmitResponse, ItemResult,
)
from app.services import lesson_engine_service

router = APIRouter(prefix="/lesson-engine", tags=["lesson-engine"])


# ---------- Admin/Teacher: CRUD items ----------
@router.post(
    "/items",
    dependencies=[Depends(require_permissions(["LESSONITEM_CREATE"]))],
    response_model=ApiResponse[LessonItemOut],
)
async def create_item(payload: LessonItemCreate, db: AsyncSession = Depends(get_db)):
    try:
        item = await lesson_engine_service.create_item(db, payload)
        # fetch choices for output
        choices_map = await lesson_engine_service.list_choices_for_items(db, [str(item.id)])
        choices = choices_map.get(str(item.id), [])
        return ApiResponse(
            data=LessonItemOut(
                id=item.id,
                lesson_id=item.lesson_id,
                item_type=item.item_type,
                prompt=item.prompt,
                content=item.content,
                points=item.points,
                sort_order=item.sort_order,
                status=item.status.value,
                choices=[
                    ChoiceOut(id=c.id, key=c.key, text=c.text, is_correct=c.is_correct, sort_order=c.sort_order)
                    for c in choices
                ] if choices else None,
            ),
            message="Created",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/items/{item_id}",
    dependencies=[Depends(require_permissions(["LESSONITEM_UPDATE"]))],
    response_model=ApiResponse[LessonItemOut],
)
async def update_item(item_id: str, payload: LessonItemUpdate, db: AsyncSession = Depends(get_db)):
    try:
        item = await lesson_engine_service.update_item(db, item_id, payload)
        choices_map = await lesson_engine_service.list_choices_for_items(db, [str(item.id)])
        choices = choices_map.get(str(item.id), [])
        return ApiResponse(
            data=LessonItemOut(
                id=item.id,
                lesson_id=item.lesson_id,
                item_type=item.item_type,
                prompt=item.prompt,
                content=item.content,
                points=item.points,
                sort_order=item.sort_order,
                status=item.status.value,
                choices=[
                    ChoiceOut(id=c.id, key=c.key, text=c.text, is_correct=c.is_correct, sort_order=c.sort_order)
                    for c in choices
                ] if choices else None,
            ),
            message="Updated",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/items/by-lesson/{lesson_id}",
    dependencies=[Depends(require_permissions(["LESSON_READ"]))],
    response_model=ApiResponse[list[LessonItemOut]],
)
async def list_items(lesson_id: str, db: AsyncSession = Depends(get_db)):
    items = await lesson_engine_service.list_items_by_lesson(db, lesson_id)
    item_ids = [str(i.id) for i in items]
    choices_map = await lesson_engine_service.list_choices_for_items(db, item_ids)

    data = []
    for i in items:
        choices = choices_map.get(str(i.id), [])
        data.append(
            LessonItemOut(
                id=i.id,
                lesson_id=i.lesson_id,
                item_type=i.item_type,
                prompt=i.prompt,
                content=i.content,
                points=i.points,
                sort_order=i.sort_order,
                status=i.status.value,
                choices=[
                    ChoiceOut(id=c.id, key=c.key, text=c.text, is_correct=c.is_correct, sort_order=c.sort_order)
                    for c in choices
                ] if choices else None,
            )
        )
    return ApiResponse(data=data)


# ---------- Student flow: start/submit attempt ----------
@router.post(
    "/lessons/{lesson_id}/attempts/start",
    dependencies=[Depends(require_permissions(["LESSON_ATTEMPT_START"]))],
    response_model=ApiResponse[AttemptStartResponse],
)
async def start_attempt(lesson_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    attempt, items, choices_map = await lesson_engine_service.start_attempt(db, user_id, lesson_id)

    items_out = []
    for i in items:
        choices = choices_map.get(str(i.id), [])
        items_out.append(
            LessonItemOut(
                id=i.id,
                lesson_id=i.lesson_id,
                item_type=i.item_type,
                prompt=i.prompt,
                content=i.content,
                points=i.points,
                sort_order=i.sort_order,
                status=i.status.value,
                # IMPORTANT: don't leak correct answers to client
                choices=[
                    ChoiceOut(id=c.id, key=c.key, text=c.text, is_correct=False, sort_order=c.sort_order)
                    for c in choices
                ] if choices else None,
            )
        )

    return ApiResponse(
        data=AttemptStartResponse(attempt_id=attempt.id, lesson_id=attempt.lesson_id, items=items_out),
        message="Started",
    )


@router.post(
    "/lessons/{lesson_id}/attempts/{attempt_id}/submit",
    dependencies=[Depends(require_permissions(["LESSON_ATTEMPT_SUBMIT"]))],
    response_model=ApiResponse[AttemptSubmitResponse],
)
async def submit_attempt(
    lesson_id: str,
    attempt_id: str,
    payload: AttemptSubmitRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        attempt, results = await lesson_engine_service.submit_attempt(
            db, user_id, lesson_id, attempt_id,
            answers={k: v.model_dump() for k, v in payload.answers.items()},
            duration_sec=payload.duration_sec,
        )
        return ApiResponse(
            data=AttemptSubmitResponse(
                attempt_id=attempt.id,
                status=attempt.status,
                score_points=attempt.score_points,
                max_points=attempt.max_points,
                score_percent=attempt.score_percent,
                results=[ItemResult(**r) for r in results],
            ),
            message="Submitted",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
