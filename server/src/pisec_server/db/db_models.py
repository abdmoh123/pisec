"""File containing schemas of tables in the SQL database."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pisec_server.api.models.camera_credentials import CameraCredentialRedactedResponse
from pisec_server.api.models.cameras import CameraResponse
from pisec_server.api.models.types.camera_columns import CameraColumns
from pisec_server.api.models.types.user_columns import UserColumns
from pisec_server.api.models.types.video_columns import VideoColumns
from pisec_server.api.models.users import UserResponse
from pisec_server.api.models.videos import VideoResponse

T_co = TypeVar("T_co", bound=BaseModel, covariant=True)


class Base(DeclarativeBase):
    """Exists to provide type hints to shutup mypy."""


class Responseable(Protocol[T_co]):
    """Protocol for objects that can be converted to a pydantic response object."""

    def to_response(self) -> T_co:
        """Convert an SQL record to a pydantic response object."""
        ...


class CameraSubscription(Base):
    """Schema for the camera_subscription table."""

    __tablename__: str = "camera_subscriptions"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    camera_id: Mapped[int] = mapped_column(Integer, ForeignKey("cameras.id"), primary_key=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class User(Base):
    """Schema for the user table."""

    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    credentials: Mapped[list[CameraCredential]] = relationship("CameraCredential", back_populates="user")
    cameras: Mapped[list[Camera]] = relationship("Camera", secondary="camera_subscriptions", back_populates="users")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship("RefreshToken", back_populates="user")

    def to_response(self) -> UserResponse:
        """Convert a User object to a UserResponse object."""
        return UserResponse.model_validate(self)

    @classmethod
    def get_column(cls, col: UserColumns) -> Mapped[Any]:  # pyright: ignore[reportExplicitAny]
        """Get a column from the User table."""
        match col:
            case UserColumns.ID:
                return cls.id
            case UserColumns.EMAIL:
                return cls.email
            case UserColumns.REGISTERED_AT:
                return cls.registered_at


class Camera(Base):
    """Schema for the camera table."""

    __tablename__: str = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    mac_address: Mapped[str] = mapped_column(String)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    users: Mapped[list[User]] = relationship("User", secondary="camera_subscriptions", back_populates="cameras")
    credential: Mapped[CameraCredential] = relationship("CameraCredential", back_populates="camera", uselist=False)
    videos: Mapped[list[Video]] = relationship("Video", back_populates="camera")

    def to_response(self) -> CameraResponse:
        """Convert a Camera object to a CameraResponse object."""
        return CameraResponse.model_validate(self)

    @classmethod
    def get_column(cls, col: CameraColumns) -> Mapped[Any]:  # pyright: ignore[reportExplicitAny]
        """Get a column from the Camera table."""
        match col:
            case CameraColumns.ID:
                return cls.id
            case CameraColumns.NAME:
                return cls.name
            case CameraColumns.MAC_ADDRESS:
                return cls.mac_address
            case CameraColumns.REGISTERED_AT:
                return cls.registered_at


class Video(Base):
    """Schema for keeping a record of uploaded videos/recordings."""

    __tablename__: str = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey(f"{Camera.__tablename__}.id"))
    file_name: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    camera: Mapped[Camera] = relationship("Camera", back_populates="videos")

    def to_response(self) -> VideoResponse:
        """Convert a Video object to a VideoResponse object."""
        return VideoResponse.model_validate(self)

    @classmethod
    def get_column(cls, col: VideoColumns) -> Mapped[Any]:  # pyright: ignore[reportExplicitAny]
        """Get a column from the Video table."""
        match col:
            case VideoColumns.ID:
                return cls.id
            case VideoColumns.CAMERA_ID:
                return cls.camera_id
            case VideoColumns.FILE_NAME:
                return cls.file_name
            case VideoColumns.UPLOADED_AT:
                return cls.uploaded_at


class CameraCredential(Base):
    """Schema for the camera_credentials table."""

    __tablename__: str = "camera_credentials"

    client_id: Mapped[str] = mapped_column(String, unique=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{User.__tablename__}.id"))
    camera_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(f"{Camera.__tablename__}.id"))
    client_secret_hash: Mapped[str] = mapped_column(String, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    user: Mapped[User] = relationship("User", back_populates="credentials")
    camera: Mapped[Camera | None] = relationship("Camera", back_populates="credential")

    def to_response(self) -> CameraCredentialRedactedResponse:
        """Convert a CameraCredential object to a CameraCredentialRedactedResponse object."""
        return CameraCredentialRedactedResponse(
            client_id=self.client_id, user_id=self.user_id, camera_id=self.camera_id, registered_at=self.registered_at
        )


class RefreshToken(Base):
    """Schema for refresh tokens, enabling session management and revocation."""

    __tablename__: str = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(f"{User.__tablename__}.id"))
    token: Mapped[str] = mapped_column(Text, unique=True, index=True)  # Text for potentially long tokens
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    device_info: Mapped[str | None] = mapped_column(String, nullable=True)  # Optional device info for specific logout

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")
