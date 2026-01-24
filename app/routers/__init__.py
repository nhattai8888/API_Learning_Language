from app.routers.auth import router as auth_router
from app.routers.rbac import router as rbac_router
from app.routers.curriculum import router as curriculum_router
from app.routers.lesson_engine import router as lesson_engine_router
from app.features.ai.router import router as ai_router
from app.routers.vocabulary import router as vocabulary_router
from app.features.review.router import router as review_router
from app.routers.grammar_engine import router as grammar_engine_router

routers = [auth_router, rbac_router, curriculum_router, lesson_engine_router, ai_router, vocabulary_router, review_router, grammar_engine_router]
