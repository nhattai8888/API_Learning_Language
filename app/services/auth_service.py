from datetime import datetime, timezone
import redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.enums import IdentityType, IdentityStatus, UserStatus, OtpPurpose, OtpChannel, SessionStatus
from app.core.security import hash_password_async, verify_password_async, needs_rehash_async
from app.models.rbac import Role, UserRole
from app.models.user import User
from app.models.auth import UserIdentity, AuthSession
from app.services.token_service import create_access_token, create_refresh_token, hash_refresh_token, refresh_expires_at
from app.services.otp_service import create_and_send_otp

async def _get_identity(db: AsyncSession, identity_type: IdentityType, value: str) -> UserIdentity | None:
    stmt = select(UserIdentity).where(UserIdentity.type == identity_type, UserIdentity.value == value)
    return (await db.execute(stmt)).scalar_one_or_none()

async def register_email(db: AsyncSession, email: str, password: str, display_name: str | None) -> User:
    existing = await _get_identity(db, IdentityType.EMAIL, email)
    if existing:
        raise ValueError("EMAIL_ALREADY_EXISTS")

    user = User(display_name=display_name, status=UserStatus.ACTIVE, password_hash=await hash_password_async(password))
    db.add(user)
    await db.flush()

    identity = UserIdentity(user_id=user.id, type=IdentityType.EMAIL, value=email, status=IdentityStatus.VERIFIED, is_primary=True)
    db.add(identity)
    await db.commit()
    await db.refresh(user)
    return user

async def register_phone_start(db: AsyncSession, phone: str, display_name: str | None, device_fingerprint: str | None):
    # If identity exists, send OTP login instead (still ok)
    identity = await _get_identity(db, IdentityType.PHONE, phone)

    if not identity:
        user = User(display_name=display_name, status=UserStatus.ACTIVE, password_hash=None)
        db.add(user)
        await db.flush()
        identity = UserIdentity(user_id=user.id, type=IdentityType.PHONE, value=phone, status=IdentityStatus.PENDING_VERIFY, is_primary=True)
        db.add(identity)
        await db.flush()
        user_id = user.id
    else:
        user_id = identity.user_id

    otp, _ = await create_and_send_otp(
        db=db,
        identity=identity,
        purpose=OtpPurpose.LOGIN_2FA,
        channel=OtpChannel.SMS,
        user_id=user_id,
        device_fingerprint=device_fingerprint,
    )
    return otp

async def login_email_start(db: AsyncSession, email: str, password: str, device_fingerprint: str | None):
    identity = await _get_identity(db, IdentityType.EMAIL, email)
    if not identity or identity.status != IdentityStatus.VERIFIED:
        raise ValueError("INVALID_CREDENTIALS")

    user = (await db.execute(select(User).where(User.id == identity.user_id))).scalar_one()
    if user.status != UserStatus.ACTIVE:
        raise ValueError("USER_INACTIVE")

    if not user.password_hash or not await verify_password_async(password, user.password_hash):
        raise ValueError("INVALID_CREDENTIALS")

    # rehash if policy changed
    if user.password_hash and await needs_rehash_async(user.password_hash):
        user.password_hash = await hash_password_async(password)

    user.last_login_at = datetime.now(timezone.utc)

    # If MFA enabled, send OTP (prefer SMS if phone exists/verified, else email)
    if user.mfa_enabled:
        # Try find verified phone
        phone_identity = (await db.execute(
            select(UserIdentity).where(UserIdentity.user_id == user.id, UserIdentity.type == IdentityType.PHONE, UserIdentity.status == IdentityStatus.VERIFIED)
        )).scalar_one_or_none()

        if phone_identity:
            otp, _ = await create_and_send_otp(db, phone_identity, OtpPurpose.LOGIN_2FA, OtpChannel.SMS, user_id=user.id, device_fingerprint=device_fingerprint)
        else:
            otp, _ = await create_and_send_otp(db, identity, OtpPurpose.LOGIN_2FA, OtpChannel.EMAIL, user_id=user.id, device_fingerprint=device_fingerprint)

        await db.commit()
        return {"mfa_required": True, "otp_id": str(otp.id)}

    # If no MFA, issue tokens directly
    tokens = await issue_tokens(db, user_id=str(user.id), device_id=None, user_agent=None, ip=None, rotated_from=None)
    await db.commit()
    return {"mfa_required": False, **tokens}

async def issue_tokens(
    db: AsyncSession,
    user_id: str,
    device_id: str | None,
    user_agent: str | None,
    ip: str | None,
    rotated_from: str | None,
):
    access = create_access_token(user_id)
    refresh = create_refresh_token()
    session = AuthSession(
        user_id=user_id,
        status=SessionStatus.ACTIVE,
        refresh_token_hash=hash_refresh_token(refresh),
        rotated_from_session_id=rotated_from,
        expires_at=refresh_expires_at(),
        ip=ip,
        user_agent=user_agent,
        device_id=device_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"access_token": access, "refresh_token": refresh, "session_id": str(session.id)}

async def rotate_refresh_token(db: AsyncSession, refresh_token: str):
    # Find active session by refresh hash
    from app.models.auth import AuthSession
    from app.core.enums import SessionStatus
    from sqlalchemy import select

    h = hash_refresh_token(refresh_token)
    session = (await db.execute(select(AuthSession).where(AuthSession.refresh_token_hash == h, AuthSession.status == SessionStatus.ACTIVE))).scalar_one_or_none()
    if not session:
        raise ValueError("INVALID_REFRESH")

    # revoke old session
    session.status = SessionStatus.REVOKED
    session.revoked_at = datetime.now(timezone.utc)

    # issue new session (rotation)
    tokens = await issue_tokens(
        db=db,
        user_id=str(session.user_id),
        device_id=session.device_id,
        user_agent=session.user_agent,
        ip=session.ip,
        rotated_from=str(session.id),
    )
    return tokens

async def revoke_session_by_refresh(db: AsyncSession, refresh_token: str) -> bool:
    h = hash_refresh_token(refresh_token)
    session = (await db.execute(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == h,
            AuthSession.status == SessionStatus.ACTIVE
        )
    )).scalar_one_or_none()

    if not session:
        return False

    session.status = SessionStatus.REVOKED
    session.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return True

async def revoke_all_sessions(db: AsyncSession, user_id: str) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.status == SessionStatus.ACTIVE)
        .values(status=SessionStatus.REVOKED, revoked_at=now)
    )
    await db.commit()
    return result.rowcount or 0

async def get_me(db: AsyncSession, user_id: str) -> dict:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user or user.status != UserStatus.ACTIVE:
        raise ValueError("USER_NOT_FOUND_OR_INACTIVE")

    # roles (lightweight)
    role_codes = (await db.execute(
        select(Role.code)
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id)
    )).scalars().all()

    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "roles": list(role_codes),
    }

async def invalidate_rbac_cache(user_id: str):
    if not redis:
        return
    await redis.delete(f"rbac:perms:{user_id}")