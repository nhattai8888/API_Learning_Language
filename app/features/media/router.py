from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.common import ApiResponse
from app.deps import require_permissions, get_current_user_id

from app.features.media.schemas import (
    CreateUploadSessionRequest, CreateUploadSessionResponse,
    FinalizeUploadRequest, MediaOut
)
from app.features.media import service

router = APIRouter(prefix="/media", tags=["media"])


@router.post(
    "/gdrive/upload-session",
    dependencies=[Depends(require_permissions(["MEDIA_UPLOAD"]))],
    response_model=ApiResponse[CreateUploadSessionResponse],
)
async def create_gdrive_upload_session(
    payload: CreateUploadSessionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    m, upload_url = await service.create_upload_session(db, user_id=str(user_id), payload=payload)
    return ApiResponse(
        data=CreateUploadSessionResponse(
            upload_url=upload_url,
            media_id=m.id,
            provider="GDRIVE",
            status="UPLOADING",
        )
    )


@router.post(
    "/gdrive/finalize",
    dependencies=[Depends(require_permissions(["MEDIA_UPLOAD"]))],
    response_model=ApiResponse[MediaOut],
)
async def finalize_gdrive_upload(
    payload: FinalizeUploadRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        m = await service.finalize_upload(
            db,
            user_id=str(user_id),
            media_id=str(payload.media_id),
            drive_file_id=payload.drive_file_id,
        )
        return ApiResponse(data=MediaOut.model_validate(m, from_attributes=True), message="READY")
    except ValueError as e:
        code = str(e)
        if code in ("MEDIA_NOT_FOUND",):
            raise HTTPException(status_code=404, detail=code)
        if code in ("FORBIDDEN",):
            raise HTTPException(status_code=403, detail=code)
        raise HTTPException(status_code=400, detail=code)


@router.get(
    "/{media_id}",
    dependencies=[Depends(require_permissions(["MEDIA_READ"]))],
    response_model=ApiResponse[MediaOut],
)
async def get_media(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        m = await service.get_media(db, user_id=str(user_id), media_id=media_id, is_admin=False)
        return ApiResponse(data=MediaOut.model_validate(m, from_attributes=True))
    except ValueError as e:
        code = str(e)
        if code == "MEDIA_NOT_FOUND":
            raise HTTPException(status_code=404, detail=code)
        if code == "FORBIDDEN":
            raise HTTPException(status_code=403, detail=code)
        raise HTTPException(status_code=400, detail=code)


@router.get(
    "",
    dependencies=[Depends(require_permissions(["MEDIA_READ"]))],
    response_model=ApiResponse[list[MediaOut]],
)
async def list_my_media(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    rows = await service.list_my_media(db, user_id=str(user_id), limit=limit, offset=offset)
    return ApiResponse(data=[MediaOut.model_validate(r, from_attributes=True) for r in rows])
