from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from app.models.curriculum import Language, Level, Unit, Lesson
from app.core.enums import PublishStatus


# ---------- Language ----------
async def create_language(db: AsyncSession, code: str, name: str, script: str | None):
    lang = Language(code=code, name=name, script=script)
    db.add(lang)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("LANGUAGE_CODE_EXISTS")
    await db.refresh(lang)
    return lang

async def update_language(db: AsyncSession, language_id: str, name: str | None, script: str | None):
    lang = await db.get(Language, language_id)
    if not lang:
        raise ValueError("LANGUAGE_NOT_FOUND")
    if name is not None:
        lang.name = name
    if script is not None:
        lang.script = script
    await db.commit()
    await db.refresh(lang)
    return lang

async def list_languages(db: AsyncSession):
    return (await db.execute(select(Language).order_by(Language.code))).scalars().all()

async def get_language(db: AsyncSession, language_id: str):
    lang = await db.get(Language, language_id)
    if not lang:
        raise ValueError("LANGUAGE_NOT_FOUND")
    return lang


# ---------- Level ----------
async def create_level(db: AsyncSession, language_id: str, code: str, name: str, sort_order: int):
    level = Level(language_id=language_id, code=code, name=name, sort_order=sort_order)
    db.add(level)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("LEVEL_CODE_EXISTS")
    await db.refresh(level)
    return level

async def update_level(db: AsyncSession, level_id: str, name: str | None, sort_order: int | None):
    lv = await db.get(Level, level_id)
    if not lv:
        raise ValueError("LEVEL_NOT_FOUND")
    if name is not None:
        lv.name = name
    if sort_order is not None:
        lv.sort_order = sort_order
    await db.commit()
    await db.refresh(lv)
    return lv

async def list_levels(db: AsyncSession, language_id: str):
    stmt = select(Level).where(Level.language_id == language_id).order_by(Level.sort_order, Level.code)
    return (await db.execute(stmt)).scalars().all()


# ---------- Unit ----------
async def create_unit(db: AsyncSession, language_id: str, level_id: str | None, title: str, description: str | None, sort_order: int):
    unit = Unit(language_id=language_id, level_id=level_id, title=title, description=description, sort_order=sort_order)
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return unit

async def update_unit(db: AsyncSession, unit_id: str, level_id: str | None, title: str | None, description: str | None, sort_order: int | None):
    unit = await db.get(Unit, unit_id)
    if not unit:
        raise ValueError("UNIT_NOT_FOUND")
    if level_id is not None:
        unit.level_id = level_id
    if title is not None:
        unit.title = title
    if description is not None:
        unit.description = description
    if sort_order is not None:
        unit.sort_order = sort_order
    await db.commit()
    await db.refresh(unit)
    return unit

async def list_units(db: AsyncSession, language_id: str, level_id: str | None = None):
    stmt = select(Unit).where(Unit.language_id == language_id)
    if level_id:
        stmt = stmt.where(Unit.level_id == level_id)
    stmt = stmt.order_by(Unit.sort_order, Unit.title)
    return (await db.execute(stmt)).scalars().all()


# ---------- Lesson ----------
async def create_lesson(
    db: AsyncSession,
    language_id: str,
    unit_id: str | None,
    title: str,
    objective: str | None,
    estimated_minutes: int,
    lesson_type,
    slug: str,
    sort_order: int,
):
    lesson = Lesson(
        language_id=language_id,
        unit_id=unit_id,
        title=title,
        objective=objective,
        estimated_minutes=estimated_minutes,
        lesson_type=lesson_type,
        slug=slug,
        sort_order=sort_order,
        publish_status=PublishStatus.DRAFT,
        version=1,
    )
    db.add(lesson)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("LESSON_SLUG_EXISTS")
    await db.refresh(lesson)
    return lesson

async def update_lesson(
    db: AsyncSession,
    lesson_id: str,
    unit_id: str | None,
    title: str | None,
    objective: str | None,
    estimated_minutes: int | None,
    lesson_type,
    publish_status,
    sort_order: int | None,
):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise ValueError("LESSON_NOT_FOUND")

    if unit_id is not None:
        lesson.unit_id = unit_id
    if title is not None:
        lesson.title = title
    if objective is not None:
        lesson.objective = objective
    if estimated_minutes is not None:
        lesson.estimated_minutes = estimated_minutes
    if lesson_type is not None:
        lesson.lesson_type = lesson_type
    if publish_status is not None:
        lesson.publish_status = publish_status
        # bump version when publish status changes to PUBLISHED (optional policy)
        if publish_status == PublishStatus.PUBLISHED:
            lesson.version += 1
    if sort_order is not None:
        lesson.sort_order = sort_order

    await db.commit()
    await db.refresh(lesson)
    return lesson

async def list_lessons(db: AsyncSession, unit_id: str, publish_status: PublishStatus | None = None):
    stmt = select(Lesson).where(Lesson.unit_id == unit_id)
    if publish_status:
        stmt = stmt.where(Lesson.publish_status == publish_status)
    stmt = stmt.order_by(Lesson.sort_order, Lesson.created_at.desc())
    return (await db.execute(stmt)).scalars().all()

async def get_lesson(db: AsyncSession, lesson_id: str):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise ValueError("LESSON_NOT_FOUND")
    return lesson
