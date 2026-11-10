"""File containing crud functions related to the CameraCredential table."""

import secrets
import uuid
from collections.abc import Callable

from argon2 import PasswordHasher
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from pisec_server.api.models.camera_credentials import CameraCredentialCreate, CameraCredentialRedactedResponse
from pisec_server.api.models.paginated.generic import PaginatedParams, PaginatedResponse
from pisec_server.core.exceptions import RecordAlreadyExistsError, RecordNotFoundError
from pisec_server.core.security.hashing import generate_hashed_password
from pisec_server.db.db_models import Camera, CameraCredential, User
from pisec_server.services.camera import get_camera
from pisec_server.services.pagination import paginate

type CredentialFilterFunc = Callable[[Select[CameraCredential]], Select[CameraCredential]]


# TODO: Use sqlalchemy select instead of query
def get_credential(db: Session, client_id: str) -> CameraCredential | None:
    """Queries the database to get a camera credential using the given ID."""
    return db.query(CameraCredential).filter(CameraCredential.client_id == client_id).first()


def get_credentials(
    db: Session,
    user_id: int,
    camera_ids: list[int] | None = None,
    skip: int = 0,
    limit: int = 100,
    with_filter: CredentialFilterFunc | None = None,
) -> PaginatedResponse[CameraCredentialRedactedResponse]:
    """Queries the database to get all camera credentials with added filtering."""
    query = select(CameraCredential).where(CameraCredential.user_id == user_id)

    if camera_ids:
        query = query.where(CameraCredential.camera_id.in_(camera_ids))

    if with_filter is not None:
        query = with_filter(query)

    params = PaginatedParams(page_index=skip // limit, page_size=limit)
    return paginate(db, query, params, CameraCredential.to_response)


def generate_credential(user: User) -> CameraCredentialCreate:
    """Generates a new credential for a given user."""
    # Credential ID includes user's name (from email) and a random UUID
    client_id: str = f"{user.email.split('@')[0]}:{uuid.uuid4().hex}"
    # Credential secret is generated randomly
    client_secret: str = secrets.token_hex(64)
    return CameraCredentialCreate(client_id=client_id, client_secret=client_secret)


def create_credential(db: Session, user_id: int, credential: CameraCredentialCreate) -> CameraCredential:
    """Creates a new camera credential using the given inputs."""
    db_credential: CameraCredential | None = get_credential(db, credential.client_id)
    if db_credential:
        raise RecordAlreadyExistsError(f"Camera credential with client ID {credential.client_id} already exists!")

    db_credential = CameraCredential(
        client_id=credential.client_id,
        user_id=user_id,
        client_secret_hash=generate_hashed_password(credential.client_secret, PasswordHasher()),
    )
    db.add(db_credential)

    db.flush()
    db.refresh(db_credential)

    return db_credential


def assign_camera(db: Session, client_id: str, camera_id: int) -> CameraCredential:
    """Assigns a camera to a given camera credential.

    NOTE: This function will not create a Camera record if it does not exist.
    """
    db_credential: CameraCredential | None = get_credential(db, client_id)
    if not db_credential:
        raise RecordNotFoundError(f"Camera credential {client_id} does not exist!")

    # Camera should be created before assigning to a credential via the camera service
    db_camera: Camera | None = get_camera(db, camera_id)
    if not db_camera:
        raise RecordNotFoundError(f"Camera {camera_id} does not exist!")

    db_credential.camera_id = camera_id

    db.flush()
    db.refresh(db_credential)

    return db_credential


def delete_credential(db: Session, client_id: str) -> CameraCredential:
    """Deletes a given camera credential by ID."""
    db_credential: CameraCredential | None = get_credential(db, client_id)

    if not db_credential:
        raise RecordNotFoundError(f"Camera credential {client_id} does not exist!")

    db.delete(db_credential)

    return db_credential
