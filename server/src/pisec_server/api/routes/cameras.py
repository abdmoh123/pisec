"""FastAPI routes related to the Camera table."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from pisec_server.api.models.camera_subscriptions import CameraSubscription
from pisec_server.api.models.cameras import CameraCreate, CameraResponse, CameraUpdate
from pisec_server.api.models.paginated.camera import CameraGetParams
from pisec_server.api.models.paginated.generic import PaginatedParams, PaginatedResponse
from pisec_server.api.models.users import UserResponse
from pisec_server.api.models.videos import VideoResponse
from pisec_server.auth.dependencies import get_current_credential, get_current_user
from pisec_server.core.exceptions import RecordNotFoundError
from pisec_server.db.database import get_db
from pisec_server.db.db_models import Camera as CameraSchema
from pisec_server.db.db_models import CameraCredential as CameraCredentialSchema
from pisec_server.db.db_models import CameraSubscription as CameraSubscriptionSchema
from pisec_server.db.db_models import User as UserSchema
from pisec_server.services import camera as camera_service
from pisec_server.services import camera_credential as camera_credential_service
from pisec_server.services import camera_subscription as subscription_service
from pisec_server.services import user as user_service
from pisec_server.services import video as video_service

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/me", response_model=CameraResponse)
def get_self(
    current_credential: Annotated[CameraCredentialSchema, Depends(get_current_credential)],
) -> CameraSchema:
    """Returns a camera's details using a given ID."""
    current_camera: CameraSchema | None = current_credential.camera
    if current_camera is None:
        raise HTTPException(status_code=403, detail="No camera linked to credential!")

    return current_camera


@router.get("/", response_model=PaginatedResponse[CameraResponse])
def get_cameras(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db)],
    params: Annotated[CameraGetParams, Query()],
) -> PaginatedResponse[CameraResponse]:
    """Gets a list of all cameras with pagination.

    Non-admin users can only see cameras they are subscribed to.
    """

    def admin_filter(q: Select[CameraSchema]) -> Select[CameraSchema]:
        if current_user.is_admin:
            return q

        # Filter to only show cameras the user is subscribed to
        subscribed_camera_ids = select(CameraSubscriptionSchema.camera_id).where(
            CameraSubscriptionSchema.user_id == current_user.id
        )
        return q.where(CameraSchema.id.in_(subscribed_camera_ids))

    cameras = camera_service.get_cameras(
        db_session,
        params.camera_id,
        params.user_id,
        params.name,
        params.mac_address,
        params.page_index * params.page_size,
        params.page_size,
        params.order_by.field,
        params.order_by.ascending,
        with_filter=admin_filter,
    )

    return cameras


@router.post("/", response_model=CameraResponse)
def create_camera(
    current_credential: Annotated[CameraCredentialSchema, Depends(get_current_credential)],
    db_session: Annotated[Session, Depends(get_db)],
    camera: Annotated[CameraCreate, Body()],
) -> CameraSchema:
    """Creates a new camera with given details."""
    if current_credential.camera_id is not None:
        raise HTTPException(status_code=400, detail="Credential already linked to Camera!")

    credential_owner: UserSchema | None = user_service.get_user(db_session, current_credential.user_id)
    if not credential_owner:
        raise HTTPException(status_code=500, detail="Camera credential somehow not registered to user!")

    # Create a new camera record along with an initial subscription (to user owner of credential)
    new_camera: CameraSchema = camera_service.create_camera(db_session, camera)
    init_subscription: list[CameraSubscription] = subscription_service.create_camera_subscriptions_by_camera(
        db_session, new_camera.id, [credential_owner.id]
    )
    if len(init_subscription) != 1:
        raise HTTPException(status_code=500, detail="Failed to create camera subscription!")

    # Add the newly created camera to the credential
    try:
        _ = camera_credential_service.assign_camera(db_session, current_credential.client_id, new_camera.id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=500, detail="Failed to assign camera to user!") from e

    return new_camera


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db)],
    camera_id: Annotated[int, Path(ge=1)],
) -> CameraSchema:
    """Returns a camera's details using a given ID."""
    db_camera: CameraSchema | None = camera_service.get_camera(db_session, camera_id)

    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found!")

    # Only allow access if user is subscribed to the camera or is an admin
    if not current_user.is_admin and db_camera not in current_user.cameras:
        raise HTTPException(status_code=403, detail="Not subscribed to this camera")

    return db_camera


@router.put("/{camera_id}", response_model=CameraResponse)
def update_camera(
    current_credential: Annotated[CameraCredentialSchema, Depends(get_current_credential)],
    db_session: Annotated[Session, Depends(get_db)],
    camera_id: Annotated[int, Path(ge=1)],
    camera: Annotated[CameraUpdate, Body()],
) -> CameraSchema:
    """Updates a camera's details using a given ID."""
    if current_credential.camera_id is None:
        raise HTTPException(status_code=403, detail="No camera linked to credential!")
    if current_credential.camera_id != camera_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this camera!")

    try:
        db_camera: CameraSchema = camera_service.update_camera(db_session, camera_id, camera)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Camera not found!") from e

    return db_camera


@router.delete("/{camera_id}", response_model=CameraResponse)
def delete_camera(
    current_credential: Annotated[CameraCredentialSchema, Depends(get_current_credential)],
    camera_id: Annotated[int, Path(ge=1)],
    db_session: Annotated[Session, Depends(get_db)],
) -> CameraSchema:
    """Deletes a given camera by ID."""
    if current_credential.camera_id is None:
        raise HTTPException(status_code=403, detail="No camera linked to credential!")
    if current_credential.camera_id != camera_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this camera!")

    try:
        db_camera: CameraSchema = camera_service.delete_camera(db_session, camera_id=camera_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Camera not found") from e

    return db_camera


@router.get("/{camera_id}/videos", response_model=PaginatedResponse[VideoResponse])
def get_videos(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db)],
    camera_id: Annotated[int, Path(ge=1)],
    pagination: Annotated[PaginatedParams, Query()],
) -> PaginatedResponse[VideoResponse]:
    """Gets a list of all of a camera's videos with pagination."""
    db_camera: CameraSchema | None = camera_service.get_camera(db_session, camera_id)
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found!")

    # Only allow access if user is subscribed to the camera or is an admin
    if not current_user.is_admin and db_camera not in current_user.cameras:
        raise HTTPException(status_code=403, detail="Not subscribed to this camera")

    # TODO: Add sorting support
    return video_service.get_video_entries(
        db_session,
        camera_ids=[db_camera.id],
        skip=pagination.page_index * pagination.page_size,
        limit=pagination.page_size,
    )


@router.get("/{camera_id}/users", response_model=PaginatedResponse[UserResponse])
def get_users(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db)],
    camera_id: Annotated[int, Path(ge=1)],
    pagination: Annotated[PaginatedParams, Query()],
) -> PaginatedResponse[UserResponse]:
    """Gets a list of all of a camera's users with pagination."""
    db_camera: CameraSchema | None = camera_service.get_camera(db_session, camera_id)
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found!")

    # Only allow access if user is subscribed to the camera or is an admin
    if not current_user.is_admin and db_camera not in current_user.cameras:
        raise HTTPException(status_code=403, detail="Not subscribed to this camera")

    # TODO: Add sorting support
    return user_service.get_users(
        db_session,
        camera_ids=[camera_id],
        skip=pagination.page_index * pagination.page_size,
        limit=pagination.page_size,
    )
