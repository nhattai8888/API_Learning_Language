from datetime import timedelta, datetime, timezone
from app.core.config import settings
from app.core.jwt import create_jwt
from app.core.security import random_token_urlsafe, sha256_hex

def create_access_token(user_id: str) -> str:
    return create_jwt({"sub": user_id, "type": "access"}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token() -> str:
    # random opaque token (not JWT), safer for rotation
    return random_token_urlsafe(48)

def hash_refresh_token(token: str) -> str:
    return sha256_hex(token)

def refresh_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
