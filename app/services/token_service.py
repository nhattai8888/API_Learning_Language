from datetime import timedelta, datetime, timezone
from app.core.config import settings
from app.core.jwt import create_jwt
from app.core.security import random_token_urlsafe, sha256_hex

def create_access_token(user_id: str) -> str:
    try:
        return create_jwt({"sub": user_id, "type": "access"}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    except Exception as e:
        raise ValueError(f"CREATE_ACCESS_TOKEN_FAILED: {str(e)}") from e

def create_refresh_token() -> str:
    try:
        # random opaque token (not JWT), safer for rotation
        return random_token_urlsafe(48)
    except Exception as e:
        raise ValueError(f"CREATE_REFRESH_TOKEN_FAILED: {str(e)}") from e

def hash_refresh_token(token: str) -> str:
    try:
        return sha256_hex(token)
    except Exception as e:
        raise ValueError(f"HASH_REFRESH_TOKEN_FAILED: {str(e)}") from e

def refresh_expires_at() -> datetime:
    try:
        return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    except Exception as e:
        raise ValueError(f"REFRESH_EXPIRES_AT_FAILED: {str(e)}") from e
