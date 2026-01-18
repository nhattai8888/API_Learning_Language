from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from app.models.curriculum import Language, Level, Unit, Lesson
from app.core.enums import PublishStatus


# ---------- Language ----------
async def create_language(db: AsyncSession, code: str, name: str, script: str | None):
    try:
        lang = Language(code=code, name=name, script=script)
        db.add(lang)
        await db.commit()
        await db.refresh(lang)
        return lang
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("LANGUAGE_CODE_EXISTS") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"CREATE_LANGUAGE_FAILED: {str(e)}") from e

async def update_language(db: AsyncSession, language_id: str, name: str | None, script: str | None):
    try:
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
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"UPDATE_LANGUAGE_FAILED: {str(e)}") from e

async def list_languages(db: AsyncSession):
    try:
        return (await db.execute(select(Language).order_by(Language.code))).scalars().all()
    except Exception as e:
        raise ValueError(f"LIST_LANGUAGES_FAILED: {str(e)}") from e

async def get_language(db: AsyncSession, language_id: str):
    try:
        lang = await db.get(Language, language_id)
        if not lang:
            raise ValueError("LANGUAGE_NOT_FOUND")
        return lang
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"GET_LANGUAGE_FAILED: {str(e)}") from e


# ---------- Level ----------
async def create_level(db: AsyncSession, language_id: str, code: str, name: str, sort_order: int):
    try:
        level = Level(language_id=language_id, code=code, name=name, sort_order=sort_order)
        db.add(level)
        await db.commit()
        await db.refresh(level)
        return level
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("LEVEL_CODE_EXISTS") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"CREATE_LEVEL_FAILED: {str(e)}") from e

async def update_level(db: AsyncSession, level_id: str, name: str | None, sort_order: int | None):
    try:
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
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"UPDATE_LEVEL_FAILED: {str(e)}") from e

async def list_levels(db: AsyncSession, language_id: str):
    try:
        stmt = select(Level).where(Level.language_id == language_id).order_by(Level.sort_order, Level.code)
        return (await db.execute(stmt)).scalars().all()
    except Exception as e:
        raise ValueError(f"LIST_LEVELS_FAILED: {str(e)}") from e


# ---------- Unit ----------
async def create_unit(db: AsyncSession, language_id: str, level_id: str | None, title: str, description: str | None, sort_order: int):
    try:
        unit = Unit(language_id=language_id, level_id=level_id, title=title, description=description, sort_order=sort_order)
        db.add(unit)
        await db.commit()
        await db.refresh(unit)
        return unit
    except Exception as e:
        await db.rollback()
        raise ValueError(f"CREATE_UNIT_FAILED: {str(e)}") from e

async def update_unit(db: AsyncSession, unit_id: str, level_id: str | None, title: str | None, description: str | None, sort_order: int | None):
    try:
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
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"UPDATE_UNIT_FAILED: {str(e)}") from e

async def list_units(db: AsyncSession, language_id: str, level_id: str | None = None):
    try:
        stmt = select(Unit).where(Unit.language_id == language_id)
        if level_id:
            stmt = stmt.where(Unit.level_id == level_id)
        stmt = stmt.order_by(Unit.sort_order, Unit.title)
        return (await db.execute(stmt)).scalars().all()
    except Exception as e:
        raise ValueError(f"LIST_UNITS_FAILED: {str(e)}") from e


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
    try:
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
        await db.commit()
        await db.refresh(lesson)
        return lesson
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("LESSON_SLUG_EXISTS") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"CREATE_LESSON_FAILED: {str(e)}") from e

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
    try:
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
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"UPDATE_LESSON_FAILED: {str(e)}") from e

async def list_lessons(db: AsyncSession, unit_id: str, publish_status: PublishStatus | None = None):
    try:
        stmt = select(Lesson).where(Lesson.unit_id == unit_id)
        if publish_status:
            stmt = stmt.where(Lesson.publish_status == publish_status)
        stmt = stmt.order_by(Lesson.sort_order, Lesson.created_at.desc())
        return (await db.execute(stmt)).scalars().all()
    except Exception as e:
        raise ValueError(f"LIST_LESSONS_FAILED: {str(e)}") from e

async def get_lesson(db: AsyncSession, lesson_id: str):
    try:
        lesson = await db.get(Lesson, lesson_id)
        if not lesson:
            raise ValueError("LESSON_NOT_FOUND")
        return lesson
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"GET_LESSON_FAILED: {str(e)}") from e
