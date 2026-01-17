from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), extra="ignore")

    APP_NAME: str = "Vocab App API"

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 5

    # Demo sending
    OTP_DEBUG_LOG: bool = True

    REDIS_URL: str = "redis://localhost:6379/0"
    RBAC_CACHE_TTL_SECONDS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_MAX_ATTEMPTS: int = 20
    
    AUTO_BOOTSTRAP: bool = True

    SUPERADMIN_EMAIL: str | None = None
    SUPERADMIN_PASSWORD: str | None = None
    SUPERADMIN_DISPLAY_NAME: str = "Super Admin"
    SUPERADMIN_PHONE: str | None = None

settings = Settings()
