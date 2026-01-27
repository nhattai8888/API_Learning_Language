from datetime import datetime
import uuid
from sqlalchemy import String, Enum, Index, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.features.media.schemas import MediaProvider, MediaStatus
from app.models.base import Base

class MediaFile(Base):
    __tablename__ = "media_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[MediaProvider] = mapped_column(
        Enum(MediaProvider, name="media_provider_enum"),
        nullable=False,
        default=MediaProvider.GDRIVE,
    )

    status: Mapped[MediaStatus] = mapped_column(
        Enum(MediaStatus, name="media_status_enum"),
        nullable=False,
        default=MediaStatus.UPLOADING,
        index=True,
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False, default="audio/wav")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    upload_url: Mapped[str | None] = mapped_column(Text)

    drive_file_id: Mapped[str | None] = mapped_column(String(128), index=True)
    drive_view_url: Mapped[str | None] = mapped_column(Text)

    # đổi tên thuộc tính Python để tránh conflict
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)

    error: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


Index("idx_media_files_user_created", MediaFile.user_id, MediaFile.created_at.desc())
Index("idx_media_files_provider_status", MediaFile.provider, MediaFile.status)