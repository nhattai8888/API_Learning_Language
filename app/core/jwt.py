from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

def create_jwt(payload: dict, expires_in: timedelta) -> str:
    now = datetime.now(timezone.utc)
    to_encode = dict(payload)
    to_encode.update({"iat": int(now.timestamp()), "exp": int((now + expires_in).timestamp())})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALG)

def decode_jwt(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALG])
