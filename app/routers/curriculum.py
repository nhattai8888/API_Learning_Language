from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.common import ApiResponse
from app.deps import require_permissions

from app.schemas.curriculum import (
    LanguageCreate, LanguageUpdate, LanguageOut,
    LevelCreate, LevelUpdate, LevelOut,
    UnitCreate, UnitUpdate, UnitOut,
    LessonCreate, LessonUpdate, LessonOut,
)
from app.core.enums import PublishStatus
from app.services import curriculum_service

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

# ----------------- Languages -----------------
@router.post(
    "/languages",
    dependencies=[Depends(require_permissions(["LESSON_CREATE"]))],
    response_model=ApiResponse[LanguageOut],
)
async def create_language(payload: LanguageCreate, db: AsyncSession = Depends(get_db)):
    try:
        lang = await curriculum_service.create_language(db, payload.code, payload.name, payload.script)
        return ApiResponse(data=LanguageOut(id=lang.id, code=lang.code, name=lang.name, script=lang.script), message="Created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/languages/{language_id}",
    dependencies=[Depends(require_permissions(["LESSON_UPDATE"]))],
    response_model=ApiResponse[LanguageOut],
)
async def update_language(language_id: str, payload: LanguageUpdate, db: AsyncSession = Depends(get_db)):
    try:
        lang = await curriculum_service.update_language(db, language_id, payload.name, payload.script)
        return ApiResponse(data=LanguageOut(id=lang.id, code=lang.code, name=lang.name, script=lang.script), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/languages", response_model=ApiResponse[list[LanguageOut]])
async def list_languages(db: AsyncSession = Depends(get_db)):
    langs = await curriculum_service.list_languages(db)
    data = [LanguageOut(id=l.id, code=l.code, name=l.name, script=l.script) for l in langs]
    return ApiResponse(data=data)

@router.get("/languages/{language_id}", response_model=ApiResponse[LanguageOut])
async def get_language(language_id: str, db: AsyncSession = Depends(get_db)):
    try:
        l = await curriculum_service.get_language(db, language_id)
        return ApiResponse(data=LanguageOut(id=l.id, code=l.code, name=l.name, script=l.script))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ----------------- Levels -----------------
@router.post(
    "/levels",
    dependencies=[Depends(require_permissions(["LESSON_CREATE"]))],
    response_model=ApiResponse[LevelOut],
)
async def create_level(payload: LevelCreate, db: AsyncSession = Depends(get_db)):
    try:
        lv = await curriculum_service.create_level(db, str(payload.language_id), payload.code, payload.name, payload.sort_order)
        return ApiResponse(data=LevelOut(id=lv.id, language_id=lv.language_id, code=lv.code, name=lv.name, sort_order=lv.sort_order), message="Created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/levels/{level_id}",
    dependencies=[Depends(require_permissions(["LESSON_UPDATE"]))],
    response_model=ApiResponse[LevelOut],
)
async def update_level(level_id: str, payload: LevelUpdate, db: AsyncSession = Depends(get_db)):
    try:
        lv = await curriculum_service.update_level(db, level_id, payload.name, payload.sort_order)
        return ApiResponse(data=LevelOut(id=lv.id, language_id=lv.language_id, code=lv.code, name=lv.name, sort_order=lv.sort_order), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/levels/by-language/{language_id}", response_model=ApiResponse[list[LevelOut]])
async def list_levels(language_id: str, db: AsyncSession = Depends(get_db)):
    levels = await curriculum_service.list_levels(db, language_id)
    data = [LevelOut(id=x.id, language_id=x.language_id, code=x.code, name=x.name, sort_order=x.sort_order) for x in levels]
    return ApiResponse(data=data)


# ----------------- Units -----------------
@router.post(
    "/units",
    dependencies=[Depends(require_permissions(["LESSON_CREATE"]))],
    response_model=ApiResponse[UnitOut],
)
async def create_unit(payload: UnitCreate, db: AsyncSession = Depends(get_db)):
    try:
        u = await curriculum_service.create_unit(
            db,
            str(payload.language_id),
            str(payload.level_id) if payload.level_id else None,
            payload.title,
            payload.description,
            payload.sort_order,
        )
        return ApiResponse(data=UnitOut(id=u.id, language_id=u.language_id, level_id=u.level_id, title=u.title, description=u.description, sort_order=u.sort_order), message="Created")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/units/{unit_id}",
    dependencies=[Depends(require_permissions(["LESSON_UPDATE"]))],
    response_model=ApiResponse[UnitOut],
)
async def update_unit(unit_id: str, payload: UnitUpdate, db: AsyncSession = Depends(get_db)):
    try:
        u = await curriculum_service.update_unit(
            db,
            unit_id,
            str(payload.level_id) if payload.level_id else None,
            payload.title,
            payload.description,
            payload.sort_order,
        )
        return ApiResponse(data=UnitOut(id=u.id, language_id=u.language_id, level_id=u.level_id, title=u.title, description=u.description, sort_order=u.sort_order), message="Updated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/units/by-language/{language_id}", response_model=ApiResponse[list[UnitOut]])
async def list_units(language_id: str, level_id: str | None = None, db: AsyncSession = Depends(get_db)):
    units = await curriculum_service.list_units(db, language_id, level_id)
    data = [UnitOut(id=u.id, language_id=u.language_id, level_id=u.level_id, title=u.title, description=u.description, sort_order=u.sort_order) for u in units]
    return ApiResponse(data=data)


# ----------------- Lessons -----------------
@router.post(
    "/lessons",
    dependencies=[Depends(require_permissions(["LESSON_CREATE"]))],
    response_model=ApiResponse[LessonOut],
)
async def create_lesson(payload: LessonCreate, db: AsyncSession = Depends(get_db)):
    try:
        ls = await curriculum_service.create_lesson(
            db,
            str(payload.language_id),
            str(payload.unit_id) if payload.unit_id else None,
            payload.title,
            payload.objective,
            payload.estimated_minutes,
            payload.lesson_type,
            payload.slug,
            payload.sort_order,
        )
        return ApiResponse(
            data=LessonOut(
                id=ls.id,
                language_id=ls.language_id,
                unit_id=ls.unit_id,
                title=ls.title,
                objective=ls.objective,
                estimated_minutes=ls.estimated_minutes,
                lesson_type=ls.lesson_type,
                publish_status=ls.publish_status,
                version=ls.version,
                slug=ls.slug,
                sort_order=ls.sort_order,
            ),
            message="Created",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/lessons/{lesson_id}",
    dependencies=[Depends(require_permissions(["LESSON_UPDATE"]))],
    response_model=ApiResponse[LessonOut],
)
async def update_lesson(lesson_id: str, payload: LessonUpdate, db: AsyncSession = Depends(get_db)):
    try:
        ls = await curriculum_service.update_lesson(
            db,
            lesson_id,
            str(payload.unit_id) if payload.unit_id else None,
            payload.title,
            payload.objective,
            payload.estimated_minutes,
            payload.lesson_type,
            payload.publish_status,
            payload.sort_order,
        )
        return ApiResponse(
            data=LessonOut(
                id=ls.id,
                language_id=ls.language_id,
                unit_id=ls.unit_id,
                title=ls.title,
                objective=ls.objective,
                estimated_minutes=ls.estimated_minutes,
                lesson_type=ls.lesson_type,
                publish_status=ls.publish_status,
                version=ls.version,
                slug=ls.slug,
                sort_order=ls.sort_order,
            ),
            message="Updated",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/lessons/by-unit/{unit_id}", response_model=ApiResponse[list[LessonOut]])
async def list_lessons(unit_id: str, publish_status: PublishStatus | None = None, db: AsyncSession = Depends(get_db)):
    lessons = await curriculum_service.list_lessons(db, unit_id, publish_status)
    data = [
        LessonOut(
            id=x.id,
            language_id=x.language_id,
            unit_id=x.unit_id,
            title=x.title,
            objective=x.objective,
            estimated_minutes=x.estimated_minutes,
            lesson_type=x.lesson_type,
            publish_status=x.publish_status,
            version=x.version,
            slug=x.slug,
            sort_order=x.sort_order,
        )
        for x in lessons
    ]
    return ApiResponse(data=data)
