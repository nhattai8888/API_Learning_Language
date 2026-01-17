from sqlalchemy import String, Text, Boolean, DateTime, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base
from app.core.enums import IdentityType, IdentityStatus, SessionStatus, OtpPurpose, OtpStatus, OtpChannel, ResetStatus

class UserIdentity(Base):
    __tablename__ = "user_identities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    type: Mapped[IdentityType] = mapped_column(Enum(IdentityType, name="identity_type_enum"), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[IdentityStatus] = mapped_column(Enum(IdentityStatus, name="identity_status_enum"), default=IdentityStatus.PENDING_VERIFY, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="identities")

class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus, name="session_status_enum"), default=SessionStatus.ACTIVE, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(Text, nullable=False)

    rotated_from_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("auth_sessions.id", ondelete="SET NULL"))
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)
    device_id: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

class TrustedDevice(Base):
    __tablename__ = "trusted_devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    device_fingerprint: Mapped[str | None] = mapped_column(Text)
    trusted_until: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class OtpChallenge(Base):
    __tablename__ = "otp_challenges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    identity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user_identities.id", ondelete="CASCADE"))

    purpose: Mapped[OtpPurpose] = mapped_column(Enum(OtpPurpose, name="otp_purpose_enum"), nullable=False)
    status: Mapped[OtpStatus] = mapped_column(Enum(OtpStatus, name="otp_status_enum"), default=OtpStatus.CREATED, nullable=False)

    code_hash: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_via: Mapped[OtpChannel] = mapped_column(Enum(OtpChannel, name="otp_channel_enum"), nullable=False)

    created_ip: Mapped[str | None] = mapped_column(String(64))
    device_fingerprint: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    identity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user_identities.id", ondelete="SET NULL"))

    status: Mapped[ResetStatus] = mapped_column(Enum(ResetStatus, name="reset_status_enum"), default=ResetStatus.PENDING, nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    used_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
