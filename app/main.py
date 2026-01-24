from fastapi import FastAPI
from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.routers import routers
from contextlib import asynccontextmanager
from app.core.cache import init_redis, close_redis
from app.services.bootstrap_service import bootstrap_all
from app.features.middleware import setup_middlewares, setup_cors


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

# Setup middleware (MUST be before app starts)
setup_middlewares(
    app=app,
    rate_limit_requests_per_minute=60,
    enable_rate_limit=True,
    enable_logging=True,
    enable_security=True,
)

# Setup CORS
setup_cors(app, allowed_origins=["*"])

for r in routers:
    app.include_router(r)

@app.get("/health")
async def health():
    return {"status": "ok"}
