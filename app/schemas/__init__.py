# app/schemas/__init__.py

from app.schemas.common import ApiResponse
from app.schemas.auth import (
    RegisterEmailRequest,
    RegisterPhoneRequest,
    LoginEmailRequest,
    LoginPhoneStartRequest,
    OtpVerifyRequest,
    RefreshRequest,
    ForgotPasswordStartRequest,
    ResetPasswordConfirmRequest,
    TokenPair,
    AuthUser,
)
from app.schemas.rbac import (
    RoleCreate,
    RoleOut,
    PermissionCreate,
    PermissionOut,
    AssignRoleRequest,
    AssignPermissionToRoleRequest,
)

from app.schemas.curriculum import (
    LanguageCreate, LanguageUpdate, LanguageOut,
    LevelCreate, LevelUpdate, LevelOut,
    UnitCreate, UnitUpdate, UnitOut,
    LessonCreate, LessonUpdate, LessonOut,
)

__all__ = [
    # common
    "ApiResponse",
    # auth
    "RegisterEmailRequest",
    "RegisterPhoneRequest",
    "LoginEmailRequest",
    "LoginPhoneStartRequest",
    "OtpVerifyRequest",
    "RefreshRequest",
    "ForgotPasswordStartRequest",
    "ResetPasswordConfirmRequest",
    "TokenPair",
    "AuthUser",
    # rbac
    "RoleCreate",
    "RoleOut",
    "PermissionCreate",
    "PermissionOut",
    "AssignRoleRequest",
    "AssignPermissionToRoleRequest",
     "LanguageCreate",
     "LanguageUpdate",
     "LanguageOut",
    "LevelCreate",
    "LevelUpdate",
    "LevelOut",
    "UnitCreate",
    "UnitUpdate",
    "UnitOut",
    "LessonCreate",
    "LessonUpdate",
    "LessonOut",
]
