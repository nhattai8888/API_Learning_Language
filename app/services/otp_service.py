import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.security import sha256_hex
from app.core.enums import OtpStatus, OtpPurpose, OtpChannel
from app.models.auth import OtpChallenge, UserIdentity

def _generate_otp_code() -> str:
    try:
        return f"{random.randint(0, 999999):06d}"
    except Exception as e:
        raise ValueError(f"GENERATE_OTP_CODE_FAILED: {str(e)}") from e

async def create_and_send_otp(
    db: AsyncSession,
    identity: UserIdentity,
    purpose: OtpPurpose,
    channel: OtpChannel,
    user_id=None,
    created_ip: str | None = None,
    device_fingerprint: str | None = None,
) -> tuple[OtpChallenge, str]:
    try:
        code = _generate_otp_code()
        otp = OtpChallenge(
            user_id=user_id,
            identity_id=identity.id,
            purpose=purpose,
            status=OtpStatus.SENT,
            code_hash=sha256_hex(code),
            attempt_count=0,
            max_attempts=settings.OTP_MAX_ATTEMPTS,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            sent_via=channel,
            created_ip=created_ip,
            device_fingerprint=device_fingerprint,
        )
        db.add(otp)
        await db.commit()
        await db.refresh(otp)

        # Replace this with real SMS/Email provider
        if settings.OTP_DEBUG_LOG:
            print(f"[OTP DEBUG] Send OTP to {identity.type}:{identity.value} code={code} otp_id={otp.id}")

        return otp, code
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("CREATE_OTP_INTEGRITY_ERROR") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"CREATE_AND_SEND_OTP_FAILED: {str(e)}") from e

async def verify_otp(db: AsyncSession, otp_id: str, code: str) -> OtpChallenge:
    try:
        stmt = select(OtpChallenge).where(OtpChallenge.id == otp_id)
        otp = (await db.execute(stmt)).scalar_one_or_none()
        if not otp:
            raise ValueError("OTP_NOT_FOUND")

        now = datetime.now(timezone.utc)
        if otp.status in (OtpStatus.VERIFIED, OtpStatus.EXPIRED, OtpStatus.LOCKED):
            await db.rollback()
            raise ValueError("OTP_INVALID_STATUS")
        if otp.expires_at <= now:
            otp.status = OtpStatus.EXPIRED
            await db.commit()
            raise ValueError("OTP_EXPIRED")

        otp.attempt_count += 1
        if otp.attempt_count > otp.max_attempts:
            otp.status = OtpStatus.LOCKED
            await db.commit()
            raise ValueError("OTP_LOCKED")

        if otp.code_hash != sha256_hex(code):
            otp.status = OtpStatus.FAILED
            await db.commit()
            raise ValueError("OTP_WRONG")

        otp.status = OtpStatus.VERIFIED
        otp.verified_at = now
        await db.commit()
        await db.refresh(otp)
        return otp
    except ValueError:
        raise
    except Exception as e:
        await db.rollback()
        raise ValueError(f"VERIFY_OTP_FAILED: {str(e)}") from e
