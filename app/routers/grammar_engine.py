from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.common import ApiResponse
from app.deps import require_permissions, get_current_user_id

from app.schemas.grammar_engine import (
    GrammarTopicCreate, GrammarTopicUpdate, GrammarTopicOut,
    GrammarPatternCreate, GrammarPatternUpdate, GrammarPatternOut,
    GrammarExampleCreate, GrammarExampleUpdate, GrammarExampleOut,
    GrammarExerciseCreate, GrammarExerciseUpdate, GrammarExerciseOut,
    GrammarChoiceCreate, GrammarChoiceUpdate, GrammarChoiceOut,
    AttachGrammarToLessonRequest, LessonGrammarOut,
    GrammarSessionResponse, GrammarSubmitRequest, GrammarSubmitResponse, GrammarSubmitResultItem,
)
from app.services import grammar_engine_service

router = APIRouter(prefix="/grammar", tags=["grammar"])


# -----------------------------
# Topics
# -----------------------------
@router.post(
    "/topics",
    dependencies=[Depends(require_permissions(["GRAMMAR_TOPIC_CREATE"]))],
    response_model=ApiResponse[GrammarTopicOut],
)
async def create_topic(payload: GrammarTopicCreate, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.create_topic(db, payload)
        return ApiResponse(data=GrammarTopicOut.model_validate(x, from_attributes=True), message="Created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/topics/{topic_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_TOPIC_UPDATE"]))],
    response_model=ApiResponse[GrammarTopicOut],
)
async def update_topic(topic_id: str, payload: GrammarTopicUpdate, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.update_topic(db, topic_id, payload)
        return ApiResponse(data=GrammarTopicOut.model_validate(x, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/topics/{topic_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_TOPIC_READ"]))],
    response_model=ApiResponse[GrammarTopicOut],
)
async def get_topic(topic_id: str, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.get_topic(db, topic_id)
        return ApiResponse(data=GrammarTopicOut.model_validate(x, from_attributes=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/topics",
    dependencies=[Depends(require_permissions(["GRAMMAR_TOPIC_READ"]))],
    response_model=ApiResponse[list[GrammarTopicOut]],
)
async def list_topics(language_id: str, status: str | None = None, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    rows = await grammar_engine_service.list_topics(db, language_id, status=status, limit=limit, offset=offset)
    return ApiResponse(data=[GrammarTopicOut.model_validate(r, from_attributes=True) for r in rows])


# -----------------------------
# Patterns
# -----------------------------
@router.post(
    "/patterns",
    dependencies=[Depends(require_permissions(["GRAMMAR_PATTERN_CREATE"]))],
    response_model=ApiResponse[GrammarPatternOut],
)
async def create_pattern(payload: GrammarPatternCreate, db: AsyncSession = Depends(get_db)):
    x = await grammar_engine_service.create_pattern(db, payload)
    return ApiResponse(data=GrammarPatternOut.model_validate(x, from_attributes=True), message="Created")


@router.patch(
    "/patterns/{pattern_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_PATTERN_UPDATE"]))],
    response_model=ApiResponse[GrammarPatternOut],
)
async def update_pattern(pattern_id: str, payload: GrammarPatternUpdate, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.update_pattern(db, pattern_id, payload)
        return ApiResponse(data=GrammarPatternOut.model_validate(x, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/patterns/{pattern_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_PATTERN_READ"]))],
    response_model=ApiResponse[GrammarPatternOut],
)
async def get_pattern(pattern_id: str, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.get_pattern(db, pattern_id)
        return ApiResponse(data=GrammarPatternOut.model_validate(x, from_attributes=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/patterns",
    dependencies=[Depends(require_permissions(["GRAMMAR_PATTERN_READ"]))],
    response_model=ApiResponse[list[GrammarPatternOut]],
)
async def list_patterns(
    language_id: str,
    topic_id: str | None = None,
    q: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    rows = await grammar_engine_service.list_patterns(db, language_id, topic_id=topic_id, q=q, status=status, limit=limit, offset=offset)
    return ApiResponse(data=[GrammarPatternOut.model_validate(r, from_attributes=True) for r in rows])


# -----------------------------
# Examples
# -----------------------------
@router.post(
    "/examples",
    dependencies=[Depends(require_permissions(["GRAMMAR_EXAMPLE_CREATE"]))],
    response_model=ApiResponse[GrammarExampleOut],
)
async def create_example(payload: GrammarExampleCreate, db: AsyncSession = Depends(get_db)):
    x = await grammar_engine_service.create_example(db, payload)
    return ApiResponse(data=GrammarExampleOut.model_validate(x, from_attributes=True), message="Created")


@router.patch(
    "/examples/{example_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_EXAMPLE_UPDATE"]))],
    response_model=ApiResponse[GrammarExampleOut],
)
async def update_example(example_id: str, payload: GrammarExampleUpdate, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.update_example(db, example_id, payload)
        return ApiResponse(data=GrammarExampleOut.model_validate(x, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/examples/by-pattern/{pattern_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_EXAMPLE_READ"]))],
    response_model=ApiResponse[list[GrammarExampleOut]],
)
async def list_examples(pattern_id: str, limit: int = 10, db: AsyncSession = Depends(get_db)):
    rows = await grammar_engine_service.list_examples_by_pattern(db, pattern_id, limit=limit)
    return ApiResponse(data=[GrammarExampleOut.model_validate(r, from_attributes=True) for r in rows])


# -----------------------------
# Exercises + Choices
# -----------------------------
@router.post(
    "/exercises",
    dependencies=[Depends(require_permissions(["GRAMMAR_EXERCISE_CREATE"]))],
    response_model=ApiResponse[GrammarExerciseOut],
)
async def create_exercise(payload: GrammarExerciseCreate, db: AsyncSession = Depends(get_db)):
    x = await grammar_engine_service.create_exercise(db, payload)
    return ApiResponse(data=GrammarExerciseOut.model_validate(x, from_attributes=True), message="Created")


@router.patch(
    "/exercises/{exercise_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_EXERCISE_UPDATE"]))],
    response_model=ApiResponse[GrammarExerciseOut],
)
async def update_exercise(exercise_id: str, payload: GrammarExerciseUpdate, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.update_exercise(db, exercise_id, payload)
        return ApiResponse(data=GrammarExerciseOut.model_validate(x, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/exercises/{exercise_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_EXERCISE_READ"]))],
    response_model=ApiResponse[GrammarExerciseOut],
)
async def get_exercise(exercise_id: str, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.get_exercise(db, exercise_id)
        return ApiResponse(data=GrammarExerciseOut.model_validate(x, from_attributes=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/exercises/by-pattern/{pattern_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_EXERCISE_READ"]))],
    response_model=ApiResponse[list[GrammarExerciseOut]],
)
async def list_exercises(pattern_id: str, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    rows = await grammar_engine_service.list_exercises_by_pattern(db, pattern_id, limit=limit, offset=offset)
    return ApiResponse(data=[GrammarExerciseOut.model_validate(r, from_attributes=True) for r in rows])


@router.post(
    "/choices",
    dependencies=[Depends(require_permissions(["GRAMMAR_CHOICE_CREATE"]))],
    response_model=ApiResponse[GrammarChoiceOut],
)
async def create_choice(payload: GrammarChoiceCreate, db: AsyncSession = Depends(get_db)):
    x = await grammar_engine_service.create_choice(db, payload)
    return ApiResponse(data=GrammarChoiceOut.model_validate(x, from_attributes=True), message="Created")


@router.patch(
    "/choices/{choice_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_CHOICE_UPDATE"]))],
    response_model=ApiResponse[GrammarChoiceOut],
)
async def update_choice(choice_id: str, payload: GrammarChoiceUpdate, db: AsyncSession = Depends(get_db)):
    try:
        x = await grammar_engine_service.update_choice(db, choice_id, payload)
        return ApiResponse(data=GrammarChoiceOut.model_validate(x, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/choices/by-exercise/{exercise_id}",
    dependencies=[Depends(require_permissions(["GRAMMAR_CHOICE_READ"]))],
    response_model=ApiResponse[list[GrammarChoiceOut]],
)
async def list_choices(exercise_id: str, db: AsyncSession = Depends(get_db)):
    rows = await grammar_engine_service.list_choices(db, exercise_id)
    return ApiResponse(data=[GrammarChoiceOut.model_validate(r, from_attributes=True) for r in rows])


# -----------------------------
# Lesson attach
# -----------------------------
@router.post(
    "/lessons/attach",
    dependencies=[Depends(require_permissions(["GRAMMAR_LESSON_ATTACH"]))],
    response_model=ApiResponse[list[LessonGrammarOut]],
)
async def attach_to_lesson(payload: AttachGrammarToLessonRequest, db: AsyncSession = Depends(get_db)):
    rows = await grammar_engine_service.attach_patterns_to_lesson(db, str(payload.lesson_id), payload.patterns)
    return ApiResponse(data=[LessonGrammarOut.model_validate(r, from_attributes=True) for r in rows], message="Attached")


@router.get(
    "/lessons/{lesson_id}/patterns",
    dependencies=[Depends(require_permissions(["GRAMMAR_LESSON_READ"]))],
    response_model=ApiResponse[list[LessonGrammarOut]],
)
async def list_lesson_patterns(lesson_id: str, db: AsyncSession = Depends(get_db)):
    rows = await grammar_engine_service.list_lesson_patterns(db, lesson_id)
    return ApiResponse(data=[LessonGrammarOut.model_validate(r, from_attributes=True) for r in rows])


# -----------------------------
# Grammar SRS session
# -----------------------------
@router.get(
    "/session",
    dependencies=[Depends(require_permissions(["GRAMMAR_SRS"]))],
    response_model=ApiResponse[GrammarSessionResponse],
)
async def start_session(language_id: str, limit: int = 10, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    data = await grammar_engine_service.start_session(db, user_id=user_id, language_id=language_id, limit=limit)

    # Convert ORM to Pydantic
    items = []
    from app.schemas.grammar import GrammarPatternOut, GrammarExampleOut, GrammarExerciseOut, GrammarChoiceOut, GrammarSessionItem

    for it in data["items"]:
        items.append(GrammarSessionItem(
            pattern=GrammarPatternOut.model_validate(it["pattern"], from_attributes=True),
            examples=[GrammarExampleOut.model_validate(x, from_attributes=True) for x in it["examples"]],
            exercise=GrammarExerciseOut.model_validate(it["exercise"], from_attributes=True) if it["exercise"] else None,
            choices=[GrammarChoiceOut.model_validate(x, from_attributes=True) for x in it["choices"]],
            state=it["state"],
        ))

    return ApiResponse(data=GrammarSessionResponse(session_id=data["session_id"], items=items, total=data["total"]))


@router.post(
    "/session/submit",
    dependencies=[Depends(require_permissions(["GRAMMAR_SRS"]))],
    response_model=ApiResponse[GrammarSubmitResponse],
)
async def submit_session(payload: GrammarSubmitRequest, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    rows = await grammar_engine_service.submit_session(
        db,
        user_id=user_id,
        language_id=str(payload.language_id),
        session_id=payload.session_id,
        items=[x.model_dump() for x in payload.items],
    )
    out = [GrammarSubmitResultItem(**r) for r in rows]
    return ApiResponse(data=GrammarSubmitResponse(updated=out, count=len(out)), message="OK")
