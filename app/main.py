from fastapi import FastAPI
from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.routers import routers
from contextlib import asynccontextmanager
from app.core.cache import init_redis, close_redis
from app.services.bootstrap_service import bootstrap_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    if settings.AUTO_BOOTSTRAP:
        async with AsyncSessionLocal() as db:
            await bootstrap_all(db)

    yield
    await close_redis()

app = FastAPI(
    title=settings.APP_NAME,
    description="API Learning Language - Vocabulary Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

for r in routers:
    app.include_router(r)

@app.get("/health")
async def health():
    return {"status": "ok"}
