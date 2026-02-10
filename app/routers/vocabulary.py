from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.common import ApiResponse
from app.deps import require_permissions, get_current_user_id

from app.schemas.vocabulary import (
    LexemeCreate, LexemeUpdate, LexemeOut,
    SenseCreate, SenseUpdate, SenseOut,
    ExampleCreate, ExampleUpdate, ExampleOut,
    AttachLexemesToLessonRequest, LessonLexemeOut,
    ReviewTodayResponse, ReviewResultRequest, WeakWordOut
)
from app.services import vocabulary_service

router = APIRouter(prefix="/vocab", tags=["vocab"])


# ---------- Lexemes ----------
@router.post(
    "/lexemes",
    dependencies=[Depends(require_permissions(["VOCAB_LEXEME_CREATE"]))],
    response_model=ApiResponse[LexemeOut],
)
async def create_lexeme(payload: LexemeCreate, db: AsyncSession = Depends(get_db)):
    try:
        x = await vocabulary_service.create_lexeme(db, payload)
        return ApiResponse(data=LexemeOut.model_validate(x, from_attributes=True), message="Created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/lexemes/{lexeme_id}",
    dependencies=[Depends(require_permissions(["VOCAB_LEXEME_UPDATE"]))],
    response_model=ApiResponse[LexemeOut],
)
async def update_lexeme(lexeme_id: str, payload: LexemeUpdate, db: AsyncSession = Depends(get_db)):
    try:
        x = await vocabulary_service.update_lexeme(db, lexeme_id, payload)
        return ApiResponse(data=LexemeOut.model_validate(x, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/lexemes/{lexeme_id}",
    dependencies=[Depends(require_permissions(["VOCAB_LEXEME_READ"]))],
    response_model=ApiResponse[LexemeOut],
)
async def get_lexeme(lexeme_id: str, db: AsyncSession = Depends(get_db)):
    try:
        x = await vocabulary_service.get_lexeme(db, lexeme_id)
        
        return ApiResponse(data=LexemeOut.model_validate(x, from_attributes=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/lexemes",
    dependencies=[Depends(require_permissions(["VOCAB_LEXEME_READ"]))],
    response_model=ApiResponse[list[LexemeOut]],
)
async def list_lexemes(language_id: str, q: str | None = None, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    rows = await vocabulary_service.list_lexemes(db, language_id, q=q, limit=limit, offset=offset)
    return ApiResponse(data=[LexemeOut.model_validate(r, from_attributes=True) for r in rows])


# ---------- Senses ----------
@router.post(
    "/senses",
    dependencies=[Depends(require_permissions(["VOCAB_SENSE_CREATE"]))],
    response_model=ApiResponse[SenseOut],
)
async def create_sense(payload: SenseCreate, db: AsyncSession = Depends(get_db)):
    try:
        s = await vocabulary_service.create_sense(db, payload)
        return ApiResponse(data=SenseOut.model_validate(s, from_attributes=True), message="Created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/senses/{sense_id}",
    dependencies=[Depends(require_permissions(["VOCAB_SENSE_UPDATE"]))],
    response_model=ApiResponse[SenseOut],
)
async def update_sense(sense_id: str, payload: SenseUpdate, db: AsyncSession = Depends(get_db)):
    try:
        s = await vocabulary_service.update_sense(db, sense_id, payload)
        return ApiResponse(data=SenseOut.model_validate(s, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/senses/by-lexeme/{lexeme_id}",
    dependencies=[Depends(require_permissions(["VOCAB_SENSE_READ"]))],
    response_model=ApiResponse[list[SenseOut]],
)
async def list_senses_by_lexeme(lexeme_id: str, db: AsyncSession = Depends(get_db)):
    
    ss = await vocabulary_service.list_senses_by_lexeme(db, lexeme_id)
    return ApiResponse(data=[SenseOut.model_validate(s, from_attributes=True) for s in ss])


# ---------- Examples ----------
@router.post(
    "/examples",
    dependencies=[Depends(require_permissions(["VOCAB_EXAMPLE_CREATE"]))],
    response_model=ApiResponse[ExampleOut],
)
async def create_example(payload: ExampleCreate, db: AsyncSession = Depends(get_db)):
    ex = await vocabulary_service.create_example(db, payload)
    return ApiResponse(data=ExampleOut.model_validate(ex, from_attributes=True), message="Created")


@router.patch(
    "/examples/{example_id}",
    dependencies=[Depends(require_permissions(["VOCAB_EXAMPLE_UPDATE"]))],
    response_model=ApiResponse[ExampleOut],
)
async def update_example(example_id: str, payload: ExampleUpdate, db: AsyncSession = Depends(get_db)):
    try:
        ex = await vocabulary_service.update_example(db, example_id, payload)
        return ApiResponse(data=ExampleOut.model_validate(ex, from_attributes=True), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/examples/by-sense/{sense_id}",
    dependencies=[Depends(require_permissions(["VOCAB_EXAMPLE_READ"]))],
    response_model=ApiResponse[list[ExampleOut]],
)
async def list_examples_by_sense(sense_id: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    exs = await vocabulary_service.list_examples_by_sense(db, sense_id, limit=limit)
    return ApiResponse(data=[ExampleOut.model_validate(e, from_attributes=True) for e in exs])


# ---------- Attach vocab to lesson ----------
@router.post(
    "/lessons/attach",
    dependencies=[Depends(require_permissions(["VOCAB_LESSON_ATTACH"]))],
    response_model=ApiResponse[list[LessonLexemeOut]],
)
async def attach_to_lesson(payload: AttachLexemesToLessonRequest, db: AsyncSession = Depends(get_db)):
    rows = await vocabulary_service.attach_lexemes_to_lesson(db, str(payload.lesson_id), payload.lexemes)
    return ApiResponse(data=[LessonLexemeOut.model_validate(r, from_attributes=True) for r in rows], message="Attached")


@router.get(
    "/lessons/{lesson_id}/lexemes",
    dependencies=[Depends(require_permissions(["VOCAB_LESSON_READ"]))],
    response_model=ApiResponse[list[LessonLexemeOut]],
)
async def list_lesson_lexemes(lesson_id: str, db: AsyncSession = Depends(get_db)):
    rows = await vocabulary_service.list_lesson_lexemes(db, lesson_id)
    return ApiResponse(data=[LessonLexemeOut.model_validate(r, from_attributes=True) for r in rows])


# ---------- Student review ----------
@router.get(
    "/review/today",
    dependencies=[Depends(require_permissions(["VOCAB_REVIEW"]))],
    response_model=ApiResponse[ReviewTodayResponse],
)
async def review_today(language_id: str, limit: int = 20, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    cards, total = await vocabulary_service.review_today(db, user_id=user_id, language_id=language_id, limit=limit)

    # pack response
    items = []
    for lx, senses, exs, st in cards:
        items.append({
            "lexeme": LexemeOut.model_validate(lx, from_attributes=True),
            "senses": [SenseOut.model_validate(s, from_attributes=True) for s in senses],
            "examples": [ExampleOut.model_validate(e, from_attributes=True) for e in exs],
            "state": {
                "mastery": st.mastery,
                "familiarity": st.familiarity,
                "ease_factor": float(st.ease_factor),
                "repetition": st.repetition,
                "interval_days": st.interval_days,
                "next_review_at": st.next_review_at,
                "last_reviewed_at": st.last_reviewed_at,
            }
        })

    return ApiResponse(data=ReviewTodayResponse(items=items, total=total))


@router.post(
    "/review/result",
    dependencies=[Depends(require_permissions(["VOCAB_REVIEW"]))],
    response_model=ApiResponse[dict],
)
async def review_result(payload: ReviewResultRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    st = await vocabulary_service.review_result(
        db,
        user_id=user_id,
        lexeme_id=str(payload.lexeme_id),
        rating=payload.rating,
        source=payload.source,
    )
    return ApiResponse(data={
        "lexeme_id": str(st.lexeme_id),
        "mastery": st.mastery,
        "familiarity": st.familiarity,
        "ease_factor": float(st.ease_factor),
        "repetition": st.repetition,
        "interval_days": st.interval_days,
        "next_review_at": st.next_review_at,
    }, message="Updated")


# ---------- Weak words ----------
@router.get(
    "/weak-words",
    dependencies=[Depends(require_permissions(["VOCAB_WEAK_WORDS"]))],
    response_model=ApiResponse[list[WeakWordOut]],
)
async def weak_words(language_id: str, limit: int = 50, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    rows = await vocabulary_service.list_weak_words(db, user_id=user_id, language_id=language_id, limit=limit)
    out = []
    for err, lx in rows:
        out.append(WeakWordOut(
            lexeme_id=lx.id,
            lemma=lx.lemma,
            type=lx.type,
            severity=err.severity,
            error_type=err.error_type,
            occur_count=err.occur_count,
            last_occurred_at=err.last_occurred_at,
            evidence=err.evidence
        ))
    return ApiResponse(data=out)
