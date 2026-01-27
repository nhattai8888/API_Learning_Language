import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.features.media.gdrive import create_resumable_upload_session, get_file_meta
from app.features.media.model import MediaFile, MediaProvider, MediaStatus  

async def create_upload_session(db: AsyncSession, user_id: str, payload):
    # create db record first
    m = MediaFile(
        user_id=user_id,
        provider=MediaProvider.GDRIVE,
        status=MediaStatus.UPLOADING,
        file_name=payload.file_name,
        mime_type=payload.mime_type,
        size_bytes=int(payload.size_bytes),
        metadata=payload.metadata,
    )
    await db.add(m)
    await db.flush()

    upload_url = await create_resumable_upload_session(
        file_name=f"{m.id}_{payload.file_name}",
        mime_type=payload.mime_type,
        size_bytes=int(payload.size_bytes),
    )

    m.upload_url = upload_url  # optional store; or store short token
    await db.commit()
    await db.refresh(m)
    return m, upload_url

async def finalize_upload(db: AsyncSession, user_id: str, media_id: str, drive_file_id: str):
    """
    Confirms file exists in Drive and marks media READY.
    """
    m = await db.get(MediaFile, media_id)
    if not m:
        raise ValueError("MEDIA_NOT_FOUND")

    # ownership gate: user can only finalize own upload (admins can override in router if you want)
    if str(m.user_id) != str(user_id):
        raise ValueError("FORBIDDEN")

    meta = await get_file_meta(drive_file_id)

    m.drive_file_id = meta.get("id")
    m.drive_view_url = meta.get("webViewLink") or meta.get("webContentLink")

    try:
        m.size_bytes = int(meta.get("size") or m.size_bytes)
    except Exception:
        pass

    m.status = MediaStatus.READY
    m.error = None
    m.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(m)
    return m

async def get_media(db: AsyncSession, user_id: str, media_id: str, is_admin: bool = False):
    m = await db.get(MediaFile, media_id)
    if not m:
        raise ValueError("MEDIA_NOT_FOUND")
    if not is_admin and str(m.user_id) != str(user_id):
        raise ValueError("FORBIDDEN")
    return m

async def list_my_media(db: AsyncSession, user_id: str, limit: int = 50, offset: int = 0):
    stmt = (
        select(MediaFile)
        .where(MediaFile.user_id == user_id)
        .order_by(MediaFile.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return (await db.execute(stmt)).scalars().all()