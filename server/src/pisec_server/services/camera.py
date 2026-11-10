"""File containing crud functions related to the Camera table."""

from collections.abc import Callable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from pisec_server.api.models.cameras import CameraCreate, CameraResponse, CameraUpdate
from pisec_server.api.models.paginated.generic import PaginatedParams, PaginatedResponse
from pisec_server.api.models.types.camera_columns import CameraColumns
from pisec_server.core.exceptions import RecordNotFoundError
from pisec_server.db.db_models import Camera, User
from pisec_server.services.pagination import paginate

type CameraFilterFunc = Callable[[Select[Camera]], Select[Camera]]


def get_camera(db: Session, camera_id: int) -> Camera | None:
    """Queries the database to get a camera using the given ID."""
    return db.query(Camera).filter(Camera.id == camera_id).first()


def get_cameras(
    db: Session,
    camera_ids: list[int] | None = None,
    user_ids: list[int] | None = None,
    camera_name: str | None = None,
    mac_address: str | None = None,
    skip: int = 0,
    limit: int = 100,
    order_by: CameraColumns = CameraColumns.ID,
    ascending: bool = True,
    with_filter: CameraFilterFunc | None = None,
) -> PaginatedResponse[CameraResponse]:
    """Queries and returns a list of cameras with pagination.

    It allows filtering by likeness as well as limiting the results to specifc cameras by IDs.
    """
    query = select(Camera)

    if camera_ids:
        query = query.where(Camera.id.in_(camera_ids))
    if user_ids:
        query = query.where(Camera.users.any(User.id.in_(user_ids)))
    if camera_name:
        query = query.where(Camera.name.ilike(f"%{camera_name}%"))
    if mac_address:
        query = query.where(Camera.mac_address.ilike(f"%{mac_address}%"))

    # Apply custom filter
    if with_filter is not None:
        query = with_filter(query)

    order_condition = Camera.get_column(order_by).asc() if ascending else Camera.get_column(order_by).desc()
    query = query.order_by(order_condition)

    params = PaginatedParams(page_index=skip // limit, page_size=limit)
    return paginate(db, query, params, Camera.to_response)


def create_camera(db: Session, camera: CameraCreate) -> Camera:
    """Creates a new camera using the given inputs."""
    db_camera = Camera(name=camera.name, mac_address=camera.mac_address)

    db.add(db_camera)
    db.flush()
    db.refresh(db_camera)

    return db_camera


def update_camera(db: Session, camera_id: int, camera: CameraUpdate) -> Camera:
    """Modifies a given camera's parameters (excluding ID) via a given ID."""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not db_camera:
        raise RecordNotFoundError(f"Camera {camera_id} does not exist!")

    # Skip modifying the database if inputs are empty or if camera doesn't exist
    if not camera.model_fields_set:
        return db_camera

    # fields left as None will not be included in the dictionary
    camera_as_dict = camera.model_dump(exclude_unset=True)

    for key, value in camera_as_dict.items():  # pyright: ignore[reportAny]
        setattr(db_camera, key, value)
    db.flush()
    db.refresh(db_camera)

    return db_camera


def delete_camera(db: Session, camera_id: int) -> Camera:
    """Deletes a given camera via ID."""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not db_camera:
        raise RecordNotFoundError(f"Camera {camera_id} does not exist!")

    db.delete(db_camera)

    return db_camera
