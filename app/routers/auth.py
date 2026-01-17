from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.deps import get_current_user_id
from app.schemas.common import ApiResponse
from app.schemas.auth import (
    LogoutRequest, MeResponse, RegisterEmailRequest, RegisterPhoneRequest,
    LoginEmailRequest, LoginPhoneStartRequest, OtpVerifyRequest,
    RefreshRequest, TokenPair
)
from app.services import auth_service
from app.services.otp_service import verify_otp
from app.models.auth import UserIdentity
from app.core.enums import IdentityType, IdentityStatus
from app.services.rbac_service import list_permissions_for_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register/email", response_model=ApiResponse[dict])
async def register_email(payload: RegisterEmailRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.register_email(db, payload.email, payload.password, payload.display_name)
        return ApiResponse(data={"user_id": str(user.id)}, message="Registered")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/register/phone/start", response_model=ApiResponse[dict])
async def register_phone_start(payload: RegisterPhoneRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        otp = await auth_service.register_phone_start(db, payload.phone, payload.display_name, None)
        return ApiResponse(data={"otp_id": str(otp.id)}, message="OTP sent")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login/email", response_model=ApiResponse[dict])
async def login_email(payload: LoginEmailRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        result = await auth_service.login_email_start(db, payload.email, payload.password, payload.device_fingerprint)
        return ApiResponse(data=result, message="OK")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login/phone/start", response_model=ApiResponse[dict])
async def login_phone_start(payload: LoginPhoneStartRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # start OTP for phone login (must exist or auto-register in register_phone_start)
    try:
        otp = await auth_service.register_phone_start(db, payload.phone, None, payload.device_fingerprint)
        return ApiResponse(data={"otp_id": str(otp.id)}, message="OTP sent")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/otp/verify", response_model=ApiResponse[TokenPair])
async def otp_verify(payload: OtpVerifyRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        otp = await verify_otp(db, payload.otp_id, payload.code)
        # Ensure identity verified for phone verification/login
        if otp.identity_id:
            identity = await db.get(UserIdentity, otp.identity_id)
            if identity and identity.status != IdentityStatus.VERIFIED:
                identity.status = IdentityStatus.VERIFIED

        user_id = str(otp.user_id) if otp.user_id else None
        if not user_id:
            raise HTTPException(status_code=400, detail="OTP missing user binding")

        tokens = await auth_service.issue_tokens(
            db=db,
            user_id=user_id,
            device_id=payload.device_id,
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host if request.client else None,
            rotated_from=None,
        )
        return ApiResponse(data=TokenPair(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"]), message="Verified")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh", response_model=ApiResponse[TokenPair])
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        tokens = await auth_service.rotate_refresh_token(db, payload.refresh_token)
        return ApiResponse(data=TokenPair(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"]), message="Refreshed")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout", response_model=ApiResponse[dict])
async def logout(payload: LogoutRequest, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """
    Revoke session by refresh_token.
    - If all_sessions=true: revoke ALL active sessions for the current user.
    """
    if payload.all_sessions:
        n = await auth_service.revoke_all_sessions(db, user_id)
        return ApiResponse(data={"revoked_sessions": n}, message="Logged out (all sessions)")

    ok = await auth_service.revoke_session_by_refresh(db, payload.refresh_token)
    if not ok:
        # idempotent logout (do not leak info)
        return ApiResponse(data={"revoked": False}, message="Logged out")
    return ApiResponse(data={"revoked": True}, message="Logged out")

@router.get("/me", response_model=ApiResponse[MeResponse])
async def me(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """
    Returns profile + roles + permissions.
    Permissions are cached (Redis) inside list_permissions_for_user.
    """
    try:
        base = await auth_service.get_me(db, user_id)
        perms = await list_permissions_for_user(db, user_id)
        data = MeResponse(
            user_id=base["user_id"],
            display_name=base["display_name"],
            roles=base["roles"],
            permissions=sorted(list(perms)),
        )
        return ApiResponse(data=data, message="OK")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))