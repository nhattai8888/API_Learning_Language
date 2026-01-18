from app.routers.auth import router as auth_router
from app.routers.rbac import router as rbac_router
from app.routers.curriculum import router as curriculum_router
from app.routers.lesson_engine import router as lesson_engine_router
from app.features.ai.router import router as ai_router

routers = [auth_router, rbac_router, curriculum_router, lesson_engine_router, ai_router]
