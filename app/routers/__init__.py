from app.routers.auth import router as auth_router
from app.routers.rbac import router as rbac_router
from app.routers.curriculum import router as curriculum_router

routers = [auth_router, rbac_router, curriculum_router]
