from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.enums import IdentityType, IdentityStatus, UserStatus, OtpPurpose, OtpChannel, SessionStatus, ResetStatus
from app.core.security import hash_password_async, verify_password_async, needs_rehash_async
from app.core.cache import redis
from app.models.rbac import Role, UserRole
from app.models.user import User
from app.models.auth import UserIdentity, AuthSession
from app.services.token_service import create_access_token, create_refresh_token, hash_refresh_token, refresh_expires_at
from app.services.otp_service import create_and_send_otp
from app.models.auth import TrustedDevice, PasswordReset, OtpChallenge
from app.core.security import sha256_hex, random_token_urlsafe
from datetime import timedelta

async def _get_identity(db: AsyncSession, identity_type: IdentityType, value: str) -> UserIdentity | None:
    try:
        stmt = select(UserIdentity).where(UserIdentity.type == identity_type, UserIdentity.value == value)
        return (await db.execute(stmt)).scalar_one_or_none()
    except Exception as e:
        raise ValueError(f"GET_IDENTITY_FAILED: {str(e)}") from e

async def register_email(db: AsyncSession, email: str, password: str, display_name: str | None) -> User:
    try:
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
    except ValueError:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("REGISTER_EMAIL_INTEGRITY_ERROR") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"REGISTER_EMAIL_FAILED: {str(e)}") from e

async def register_phone_start(db: AsyncSession, phone: str, display_name: str | None, device_fingerprint: str | None):
    try:
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
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("REGISTER_PHONE_INTEGRITY_ERROR") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"REGISTER_PHONE_START_FAILED: {str(e)}") from e

async def login_email_start(db: AsyncSession, email: str, password: str, device_fingerprint: str | None):
    try:
        identity = await _get_identity(db, IdentityType.EMAIL, email)
        if not identity or identity.status != IdentityStatus.VERIFIED:
            raise ValueError("INVALID_CREDENTIALS")

        user = (await db.execute(select(User).where(User.id == identity.user_id))).scalar_one_or_none()
        if not user or user.status != UserStatus.ACTIVE:
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
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"LOGIN_EMAIL_START_FAILED: {str(e)}") from e

async def issue_tokens(
    db: AsyncSession,
    user_id: str,
    device_id: str | None,
    user_agent: str | None,
    ip: str | None,
    rotated_from: str | None,
):
    try:
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
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("ISSUE_TOKENS_INTEGRITY_ERROR") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"ISSUE_TOKENS_FAILED: {str(e)}") from e

async def rotate_refresh_token(db: AsyncSession, refresh_token: str):
    try:
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
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"ROTATE_REFRESH_TOKEN_FAILED: {str(e)}") from e

async def revoke_session_by_refresh(db: AsyncSession, refresh_token: str) -> bool:
    try:
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
    except Exception as e:
        await db.rollback()
        raise ValueError(f"REVOKE_SESSION_BY_REFRESH_FAILED: {str(e)}") from e

async def revoke_all_sessions(db: AsyncSession, user_id: str) -> int:
    try:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.status == SessionStatus.ACTIVE)
            .values(status=SessionStatus.REVOKED, revoked_at=now)
        )
        await db.commit()
        return result.rowcount or 0
    except Exception as e:
        await db.rollback()
        raise ValueError(f"REVOKE_ALL_SESSIONS_FAILED: {str(e)}") from e

async def get_me(db: AsyncSession, user_id: str) -> dict:
    try:
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
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"GET_ME_FAILED: {str(e)}") from e

async def invalidate_rbac_cache(user_id: str):
    try:
        if not redis:
            return
        await redis.delete(f"rbac:perms:{user_id}")
    except Exception as e:
        # Log but don't fail - cache invalidation is non-critical
        print(f"[WARN] INVALIDATE_RBAC_CACHE_FAILED: {str(e)}")


async def create_trusted_device(db: AsyncSession, user_id: str, device_id: str | None, device_fingerprint: str | None, days: int = 30):
    try:
        now = datetime.now(timezone.utc)
        trusted_until = now + timedelta(days=days)

        # try update existing by device_id or fingerprint
        stmt = None
        existing = None
        if device_id:
            existing = await db.execute(select(TrustedDevice).where(TrustedDevice.user_id == user_id, TrustedDevice.device_id == device_id))
            existing = existing.scalar_one_or_none()

        if not existing and device_fingerprint:
            existing = await db.execute(select(TrustedDevice).where(TrustedDevice.user_id == user_id, TrustedDevice.device_fingerprint == device_fingerprint))
            existing = existing.scalar_one_or_none()

        if existing:
            existing.trusted_until = trusted_until
            await db.commit()
            return existing

        td = TrustedDevice(user_id=user_id, device_id=device_id or "", device_fingerprint=device_fingerprint, trusted_until=trusted_until)
        db.add(td)
        await db.commit()
        await db.refresh(td)
        return td
    except Exception as e:
        await db.rollback()
        raise ValueError(f"CREATE_TRUSTED_DEVICE_FAILED: {str(e)}") from e


async def biometric_login(db: AsyncSession, device_id: str | None, device_fingerprint: str | None, user_agent: str | None, ip: str | None):
    try:
        now = datetime.now(timezone.utc)
        td = None
        if device_id:
            td = (await db.execute(select(TrustedDevice).where(TrustedDevice.device_id == device_id, TrustedDevice.trusted_until >= now))).scalar_one_or_none()
        if not td and device_fingerprint:
            td = (await db.execute(select(TrustedDevice).where(TrustedDevice.device_fingerprint == device_fingerprint, TrustedDevice.trusted_until >= now))).scalar_one_or_none()

        if not td:
            raise ValueError("TRUSTED_DEVICE_NOT_FOUND_OR_EXPIRED")

        # Issue tokens for the associated user
        tokens = await issue_tokens(db, user_id=str(td.user_id), device_id=td.device_id, user_agent=user_agent, ip=ip, rotated_from=None)
        return tokens
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"BIOMETRIC_LOGIN_FAILED: {str(e)}") from e


async def forgot_password_start(db: AsyncSession, identity_type: IdentityType, value: str) -> str:
    try:
        identity = await _get_identity(db, identity_type, value)
        if not identity:
            raise ValueError("IDENTITY_NOT_FOUND")

        token = random_token_urlsafe(16)
        token_hash = sha256_hex(token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=60)

        pr = PasswordReset(user_id=identity.user_id, identity_id=identity.id, status=ResetStatus.PENDING, token_hash=token_hash, expires_at=expires_at)
        db.add(pr)
        await db.commit()
        await db.refresh(pr)

        # In production send token via email/SMS. Return token for debug/testing
        return token
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("FORGOT_PASSWORD_INTEGRITY_ERROR") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"FORGOT_PASSWORD_START_FAILED: {str(e)}") from e


async def reset_password_confirm(db: AsyncSession, token: str, new_password: str):
    try:
        token_hash = sha256_hex(token)
        now = datetime.now(timezone.utc)
        stmt = select(PasswordReset).where(PasswordReset.token_hash == token_hash, PasswordReset.status == ResetStatus.PENDING)
        pr = (await db.execute(stmt)).scalar_one_or_none()
        if not pr:
            raise ValueError("INVALID_OR_USED_TOKEN")
        if pr.expires_at <= now:
            pr.status = ResetStatus.EXPIRED
            await db.commit()
            raise ValueError("TOKEN_EXPIRED")

        user = (await db.execute(select(User).where(User.id == pr.user_id))).scalar_one_or_none()
        if not user:
            raise ValueError("USER_NOT_FOUND")

        user.password_hash = await hash_password_async(new_password)
        pr.status = ResetStatus.USED
        pr.used_at = now
        await db.commit()
        return True
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"RESET_PASSWORD_FAILED: {str(e)}") from e