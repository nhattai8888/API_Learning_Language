from app.routers.auth import router as auth_router
from app.routers.rbac import router as rbac_router

routers = [auth_router, rbac_router]
