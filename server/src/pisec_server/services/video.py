"""File containing crud functions related to the Video table."""

import mimetypes
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session

from pisec_server.api.models.paginated.generic import PaginatedParams, PaginatedResponse
from pisec_server.api.models.types.video_columns import VideoColumns
from pisec_server.api.models.videos import VideoDeleteResult, VideoFileData, VideoResponse, VideoUpdate
from pisec_server.core.exceptions import RecordNotFoundError
from pisec_server.core.validation.video_validation import get_video_file_path_safe
from pisec_server.db.db_models import Camera, Video
from pisec_server.services.camera import get_camera
from pisec_server.services.pagination import paginate

type VideoFilterFunc = Callable[[Select[Video]], Select[Video]]


def get_video_file_data(video: Video) -> VideoFileData:
    """Gets the path and name for the video file along with the mimetype."""
    # Get video file path and validate it
    file_path: Path = get_video_file_path_safe(video.file_name, video.camera_id)
    if not file_path.exists():
        raise FileNotFoundError(f"Video file {file_path} does not exist!")

    # Get mime type of the file (will probably always be video/mp4)
    media_type, _ = mimetypes.guess_type(video.file_name)
    media_type = media_type or "application/octet-stream"

    return VideoFileData(file_path=file_path, file_name=video.file_name, media_type=media_type)


def get_video_entry(db: Session, video_id: int) -> Video | None:
    """Queries the database to get a video entry using the given ID."""
    return db.query(Video).filter(Video.id == video_id).first()


def get_video_entries(
    db: Session,
    video_ids: list[int] | None = None,
    file_name: str | None = None,
    camera_ids: list[int] | None = None,
    skip: int = 0,
    limit: int = 100,
    order_by: VideoColumns = VideoColumns.ID,
    ascending: bool = True,
    with_filter: VideoFilterFunc | None = None,
) -> PaginatedResponse[VideoResponse]:
    """Queries and returns a list of videos with pagination.

    Allows filtering by likeness and also limiting results to chosen list of IDs.
    """
    query = select(Video)

    if video_ids:
        query = query.where(Video.id.in_(video_ids))
    if file_name:
        query = query.where(Video.file_name.ilike(f"%{file_name}%"))
    if camera_ids:
        query = query.where(Video.camera_id.in_(camera_ids))

    # Apply any custom filter
    if with_filter is not None:
        query = with_filter(query)

    order_condition = Video.get_column(order_by).asc() if ascending else Video.get_column(order_by).desc()
    query = query.order_by(order_condition)

    params = PaginatedParams(page_index=skip // limit, page_size=limit)
    return paginate(db, query, params, Video.to_response)


def create_video_entry(db: Session, file_name: str, camera_id: int) -> Video:
    """Creates a new video entry using the given inputs."""
    # Check if the camera exists before creating the video entry
    db_camera: Camera | None = get_camera(db, camera_id)
    if not db_camera:
        raise RecordNotFoundError(f"Failed to create video: Camera {camera_id} does not exist!")

    db_video = Video(file_name=file_name, camera_id=db_camera.id)

    db.add(db_video)

    return db_video


def update_video_entry(db: Session, video_id: int, new_video_data: VideoUpdate) -> Video:
    """Modifies a given video entry's parameters (excluding ID) via a given ID.

    You can only modify the name of the video for now.
    """
    db_video: Video | None = get_video_entry(db, video_id)
    # Skip modifying the database if video doesn't exist
    if not db_video:
        raise RecordNotFoundError(f"Video {video_id} does not exist!")

    # Skip modifying the database if inputs are empty
    if not new_video_data.model_fields_set:
        return db_video

    if new_video_data.file_name:
        db_video.file_name = new_video_data.file_name

    return db_video


def delete_video_entries(
    db: Session,
    video_ids: list[int] | None = None,
    file_name: str | None = None,
    camera_ids: list[int] | None = None,
) -> list[Video]:
    """Deletes a list of videos."""
    query = delete(Video).returning(Video)

    if video_ids:
        query = query.where(Video.id.in_(video_ids))
    if file_name:
        query = query.where(Video.file_name.ilike(f"%{file_name}%"))
    if camera_ids:
        query = query.where(Video.camera_id.in_(camera_ids))

    result = db.execute(query).scalars().all()
    for row in result:
        db.expunge(row)

    return list(result)


def delete_video_entry(db: Session, video_id: int) -> Video:
    """Deletes a given video entry via ID."""
    db_video = db.query(Video).filter(Video.id == video_id).first()

    if not db_video:
        raise RecordNotFoundError(f"Video {video_id} does not exist!")

    db.delete(db_video)

    return db_video


def delete_videos(
    db: Session,
    video_ids: list[int] | None = None,
    file_name: str | None = None,
    camera_ids: list[int] | None = None,
    with_filter: VideoFilterFunc | None = None,
) -> VideoDeleteResult:
    """Deletes video entries and files."""
    # Get videos without pagination
    query = select(Video)
    if video_ids:
        query = query.where(Video.id.in_(video_ids))
    if file_name:
        query = query.where(Video.file_name.ilike(f"%{file_name}%"))
    if camera_ids:
        query = query.where(Video.camera_id.in_(camera_ids))

    if with_filter is not None:
        query = with_filter(query)

    result = db.execute(query).scalars().all()
    for row in result:
        db.expunge(row)
    videos_to_delete = list(result)

    successful_deletes: list[int] = []
    failed_deletes: list[int] = []
    for video in videos_to_delete:
        try:
            db.delete(video)
            file_path = get_video_file_path_safe(video.file_name, video.camera_id)
            file_path.unlink(missing_ok=True)

            db.commit()
            successful_deletes.append(video.id)
        except Exception:  # noqa: BLE001
            db.rollback()
            failed_deletes.append(video.id)

    return VideoDeleteResult(deleted=successful_deletes, failed=failed_deletes)
