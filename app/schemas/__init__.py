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
]
