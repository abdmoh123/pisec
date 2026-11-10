"""FastAPI routes related to the Video table."""

from pathlib import Path as FilePath
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Path, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from pisec_server.api.models.paginated.generic import PaginatedResponse
from pisec_server.api.models.paginated.video import VideoGetParams
from pisec_server.api.models.videos import Video, VideoFileData, VideoResponse, VideoUpdate, VideoUrlResponse
from pisec_server.auth.dependencies import get_current_credential, get_current_user, get_current_user_optional
from pisec_server.core.exceptions import InvalidFileNameError, RecordAlreadyExistsError, RecordNotFoundError
from pisec_server.core.validation.regex import file_name_regex
from pisec_server.core.validation.video_validation import get_video_file_path_safe
from pisec_server.db.cache_store import nonce_store
from pisec_server.db.database import get_db
from pisec_server.db.db_models import Camera, CameraSubscription
from pisec_server.db.db_models import CameraCredential as CameraCredentialSchema
from pisec_server.db.db_models import User as UserSchema
from pisec_server.db.db_models import Video as VideoSchema
from pisec_server.services import camera as camera_service
from pisec_server.services import user as user_service
from pisec_server.services import video as video_service
from pisec_server.services import video_url as video_url_service

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/", response_model=PaginatedResponse[VideoResponse])
def get_videos(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db)],
    params: Annotated[VideoGetParams, Query()],
) -> PaginatedResponse[VideoResponse]:
    """Gets a list of all videos with pagination.

    Non-admin users can only see videos from cameras they are subscribed to.
    """

    def admin_filter(q: Select[VideoSchema]) -> Select[VideoSchema]:
        if current_user.is_admin:
            return q

        # Filter to only show videos from cameras user is subscribed to
        subscribed_camera_ids = select(CameraSubscription.camera_id).where(
            CameraSubscription.user_id == current_user.id
        )
        return q.where(VideoSchema.camera_id.in_(subscribed_camera_ids))

    return video_service.get_video_entries(
        db_session,
        params.video_id,
        params.file_name,
        params.camera_id,
        skip=params.page_index * params.page_size,
        limit=params.page_size,
        order_by=params.order_by.field,
        ascending=params.order_by.ascending,
        with_filter=admin_filter,
    )


@router.post("/", response_model=Video)
async def upload_video(
    current_credential: Annotated[CameraCredentialSchema, Depends(get_current_credential)],
    file_name: Annotated[str, Form(pattern=file_name_regex, min_length=5)],
    video_file: Annotated[UploadFile, File()],
    db_session: Annotated[Session, Depends(get_db)],
) -> VideoSchema:
    """Creates and uploads a new video with the given details."""
    if not current_credential.camera_id:
        raise HTTPException(status_code=403, detail="No camera registered with this credential!")

    # Check if video entry already exists in the database (file name and camera ID must be the same)
    db_videos: PaginatedResponse[VideoResponse] = await run_in_threadpool(
        video_service.get_video_entries,
        db_session,
        file_name=file_name,
        camera_ids=[current_credential.camera_id],
        skip=0,
        limit=1,
    )
    if db_videos.items:
        raise HTTPException(status_code=400, detail="Video already exists!")

    # Check if the uploaded file is a video
    if video_file.content_type is None or "video" not in video_file.content_type:
        raise HTTPException(status_code=415, detail="File uploaded is not a video!")

    # TODO: Make the video files get stored on the database container instead of api server
    try:
        file_path: FilePath = get_video_file_path_safe(file_name, current_credential.camera_id)
    except InvalidFileNameError as e:
        raise HTTPException(status_code=400, detail="Invalid file name!") from e
    # Make sure the directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the video entry
    try:
        result_video: VideoSchema = await run_in_threadpool(
            video_service.create_video_entry,
            db_session,
            file_name,
            current_credential.camera_id,
        )
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Camera not found!") from e

    # Write the uploaded video to the server's storage (async part)
    # The file writing is done last as it can be the slowest
    try:
        video_contents: bytes = await video_file.read()
        async with aiofiles.open(file_path, "wb") as file:
            _ = await file.write(video_contents)
    except Exception as e:  # noqa: BLE001
        file_path.unlink(missing_ok=True)
        # Any changes to the database will be rolled back if any error is raised
        # See get_db() in pisec_server.db.databse
        raise HTTPException(status_code=500, detail=f"Failed to upload video file: {e!s}")

    return result_video


@router.get("/{video_id}/url")
def generate_video_url(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    video_id: Annotated[int, Path(ge=1)],
    request: Request,
    db_session: Annotated[Session, Depends(get_db)],
) -> VideoUrlResponse:
    """Creates a signed URL for downloading a video."""
    db_video: VideoSchema | None = video_service.get_video_entry(db_session, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found!")

    token_record = video_url_service.generate_signed_download_token(video_id, current_user.id)

    download_url = request.url_for("download_video", video_id=video_id)
    download_url = download_url.include_query_params(token=token_record.token)

    return VideoUrlResponse(url=str(download_url), expires_at=token_record.expires_at)


@router.get("/{video_id}/file", name="download_video")
async def download_video(
    current_user: Annotated[UserSchema | None, Depends(get_current_user_optional)],
    token: Annotated[str | None, Query()],
    video_id: Annotated[int, Path(ge=1)],
    db_session: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    """Endpoint for downloading a video."""
    user_id: int | None = None
    # Ignore authourisation if token exists and is valid
    if token is not None:
        try:
            payload = video_url_service.decode_signed_download_token(token)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        # Check if the token is valid or not (expiry and video ID match)
        try:
            video_url_service.assert_token_validity(payload, video_id)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e)) from e
        user_id = payload.user_id

        # Mark token as used and assert that it hasn't been used before
        try:
            await nonce_store.consume_nonce(payload)
        except RecordAlreadyExistsError as e:
            raise HTTPException(status_code=401, detail="Token already used! Please request a new url.") from e
    else:
        if current_user is None:
            raise HTTPException(status_code=401, detail="Token missing and user not authenticated!")
        user_id = current_user.id

    # WARN: You can't use asyncio.gather here because the db_session is shared and not thread safe
    db_user: UserSchema | None = await run_in_threadpool(user_service.get_user, db_session, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found!")

    db_video: VideoSchema | None = await run_in_threadpool(video_service.get_video_entry, db_session, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found!")

    valid_users = await run_in_threadpool(lambda: db_video.camera.users)
    # Only allow access if the user is subscribed to the camera or is an admin
    if not db_user.is_admin and db_user not in valid_users:
        raise HTTPException(status_code=403, detail="Not subscribed to this camera")

    # Get video file data
    try:
        video_file_data: VideoFileData = await run_in_threadpool(video_service.get_video_file_data, db_video)
    except InvalidFileNameError as e:
        raise HTTPException(status_code=500, detail="Invalid file path!") from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail="Video file not found!") from e

    return FileResponse(
        path=video_file_data.file_path, filename=video_file_data.file_name, media_type=video_file_data.media_type
    )


@router.get("/{video_id}", response_model=Video)
def get_video(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    video_id: Annotated[int, Path(ge=1)],
    db_session: Annotated[Session, Depends(get_db)],
) -> VideoSchema:
    """Returns a video's details using a given ID.

    Users can only see videos from cameras they are subscribed to, or admins can see all.
    """
    db_video: VideoSchema | None = video_service.get_video_entry(db_session, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found!")

    # Only allow access if the user is subscribed to the camera or is an admin
    db_camera: Camera | None = camera_service.get_camera(db_session, db_video.camera_id)
    if db_camera and not current_user.is_admin and db_camera not in current_user.cameras:
        raise HTTPException(status_code=403, detail="Not subscribed to this camera")

    return db_video


@router.put("/{video_id}", response_model=Video)
def update_video(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    video_id: Annotated[int, Path(ge=1)],
    video: Annotated[VideoUpdate, Body()],
    db_session: Annotated[Session, Depends(get_db)],
) -> VideoSchema:
    """Updates a video's details using a given ID.

    Users can only update videos from cameras they are subscribed to, or admins can update all.
    """
    db_video: VideoSchema | None = video_service.get_video_entry(db_session, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found!")

    # Only allow updates if the user is subscribed to the camera or is an admin
    db_camera: Camera | None = camera_service.get_camera(db_session, db_video.camera_id)
    if db_camera and not current_user.is_admin and db_camera not in current_user.cameras:
        raise HTTPException(status_code=403, detail="Not subscribed to this camera")

    try:
        db_video = video_service.update_video_entry(db_session, video_id, video)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Video not found!") from e

    return db_video


@router.delete("/{video_id}", response_model=Video)
def delete_video(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    video_id: Annotated[int, Path(ge=1)],
    db_session: Annotated[Session, Depends(get_db)],
) -> VideoSchema:
    """Deletes a given video.

    Users can only delete videos from cameras they are subscribed to, or admins can delete all.
    """
    db_video: VideoSchema | None = video_service.get_video_entry(db_session, video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found!")

    # Only allow deletion if the user is subscribed to the camera or is an admin
    db_camera: Camera | None = camera_service.get_camera(db_session, db_video.camera_id)
    if db_camera and not current_user.is_admin and db_camera not in current_user.cameras:
        raise HTTPException(status_code=403, detail="Not subscribed to this camera")

    # Delete the video entry
    # NOTE: This will rollback if any later step failed
    try:
        deleted_video: VideoSchema = video_service.delete_video_entry(db_session, video_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail="Failed to delete: Video not found!") from e

    # Get file path
    try:
        file_path: FilePath = get_video_file_path_safe(deleted_video.file_name, deleted_video.camera_id)
    except InvalidFileNameError as e:
        raise HTTPException(status_code=500, detail="Invalid file path!") from e

    # Delete the video file
    try:
        file_path.unlink()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Failed to delete: Video not found!") from e

    return deleted_video
