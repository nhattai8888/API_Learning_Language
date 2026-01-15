from sqlalchemy import String, Text, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base
from app.core.enums import UserSegment, UserStatus

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str | None] = mapped_column(String(100))
    user_segment: Mapped[UserSegment] = mapped_column(Enum(UserSegment, name="user_segment_enum"), default=UserSegment.GENERAL, nullable=False)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus, name="user_status_enum"), default=UserStatus.ACTIVE, nullable=False)

    password_hash: Mapped[str | None] = mapped_column(Text)

    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    identities = relationship("UserIdentity", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
