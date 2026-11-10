"""File containing crud functions related to handling camera subscriptions."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from pisec_server.api.models.camera_subscriptions import CameraSubscription
from pisec_server.core.exceptions import RecordAlreadyExistsError, RecordNotFoundError
from pisec_server.db.db_models import Camera, User
from pisec_server.db.db_models import CameraSubscription as CameraSubscriptionSchema
from pisec_server.services.camera import get_camera, get_cameras
from pisec_server.services.user import get_user, get_users


def get_camera_subscriptions_by_user(db: Session, user_id: int) -> list[CameraSubscription]:
    """Gets all camera subscriptions of the given user."""
    db_user: User | None = get_user(db, user_id)
    if not db_user:
        raise RecordNotFoundError(f"User {user_id} does not exist!")

    # NOTE: Number of subscriptions could be empty
    subscriptions: list[CameraSubscription] = []
    for camera in db_user.cameras:
        subscriptions.append(CameraSubscription(user_id=db_user.id, camera_id=camera.id))

    return subscriptions


def get_camera_subscriptions_by_camera(db: Session, camera_id: int) -> list[CameraSubscription]:
    """Returns all subscriptions a given camera is assigned to."""
    db_camera: Camera | None = get_camera(db, camera_id)
    if not db_camera:
        raise RecordNotFoundError(f"Camera {camera_id} does not exist!")

    # NOTE: Number of subscriptions could be empty
    subscriptions: list[CameraSubscription] = []
    for user in db_camera.users:
        subscriptions.append(CameraSubscription(user_id=user.id, camera_id=camera_id))

    return subscriptions


def get_camera_subscriptions(
    db: Session, user_ids: list[int] | None = None, camera_ids: list[int] | None = None
) -> list[CameraSubscriptionSchema]:
    """Queries and returns a list of camera subscriptions."""
    query = select(CameraSubscriptionSchema)

    if user_ids:
        query = query.where(CameraSubscriptionSchema.user_id.in_(user_ids))
    if camera_ids:
        query = query.where(CameraSubscriptionSchema.camera_id.in_(camera_ids))

    return list(db.execute(query).scalars().all())


def create_camera_subscriptions_by_user(db: Session, user_id: int, camera_ids: list[int]) -> list[CameraSubscription]:
    """Subscribes the given user to the given cameras."""
    db_user: User | None = get_user(db, user_id)
    # Don't bother subscribing if the user doesn't exist
    if not db_user:
        raise RecordNotFoundError(f"User {user_id} does not exist!")

    # Separate out the cameras that the user is already subscribed to
    current_subscription_ids: list[int] = [sub.camera_id for sub in get_camera_subscriptions_by_user(db, user_id)]
    real_cameras = get_cameras(db, camera_ids, limit=len(camera_ids)).items
    unsubscribed_cameras = [camera for camera in real_cameras if camera.id not in current_subscription_ids]

    if not unsubscribed_cameras:
        raise RecordAlreadyExistsError(f"User {user_id} is already subscribed to all given cameras!")

    # Add the new camera subscriptions
    result: list[CameraSubscription] = []
    for camera in unsubscribed_cameras:
        result.append(CameraSubscription(user_id=db_user.id, camera_id=camera.id))

    db.add_all(result)
    db.flush()

    return result


def create_camera_subscriptions_by_camera(db: Session, camera_id: int, user_ids: list[int]) -> list[CameraSubscription]:
    """Subscribes users to the given camera."""
    db_camera: Camera | None = get_camera(db, camera_id)
    # Don't bother subscribing if the user doesn't exist
    if not db_camera:
        raise RecordNotFoundError(f"Camera {camera_id} does not exist!")

    # Separate out the cameras that the user is already subscribed to
    current_subscription_ids: list[int] = [sub.user_id for sub in get_camera_subscriptions_by_camera(db, camera_id)]
    real_users = get_users(db, user_ids, limit=len(user_ids)).items
    unsubscribed_users = [user for user in real_users if user.id not in current_subscription_ids]

    if not unsubscribed_users:
        raise RecordAlreadyExistsError(f"Camera {camera_id} is already subscribed to all given users!")

    # Add the new camera subscriptions
    result: list[CameraSubscription] = []
    for user in unsubscribed_users:
        result.append(CameraSubscription(user_id=user.id, camera_id=camera_id))

    db.add_all(result)
    db.flush()

    return result


def delete_camera_subscriptions(
    db: Session, user_ids: list[int] | None = None, camera_ids: list[int] | None = None
) -> list[CameraSubscriptionSchema]:
    """Deletes a list of subscriptions that fit the given parameters."""
    if camera_ids is not None:
        # Check if all cameras exist
        search_query = select(Camera.id).where(Camera.id.in_(camera_ids))
        real_camera_ids: set[int] = set(db.execute(search_query).scalars().all())
        missing_camera_ids = set(camera_ids) - real_camera_ids
        if missing_camera_ids:
            raise RecordNotFoundError(f"Following cameras were not found: {missing_camera_ids}")

    query = delete(CameraSubscriptionSchema).returning(CameraSubscriptionSchema)

    # The given IDs are combined in an AND fashion
    if user_ids:
        query = query.where(CameraSubscriptionSchema.user_id.in_(user_ids))
    if camera_ids:
        query = query.where(CameraSubscriptionSchema.camera_id.in_(camera_ids))

    result = db.execute(query).scalars().all()
    # Prevent error with fastapi accessing data that no longer exists
    for row in result:
        db.expunge(row)

    return list(result)
