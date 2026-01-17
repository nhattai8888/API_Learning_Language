from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.core.jwt import decode_jwt
from app.services.rbac_service import list_permissions_for_user

async def get_current_user_id(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_jwt(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload["sub"]

def require_permissions(required: list[str]):
    async def _guard(
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ):
        perms = await list_permissions_for_user(db, user_id)
        missing = [p for p in required if p not in perms]
        if missing:
            raise HTTPException(status_code=403, detail=f"Missing permissions: {missing}")
        return True
    return _guard
