from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
settings = Settings()
