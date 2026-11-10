"""File containing crud functions related to the User table."""

from collections.abc import Callable

from argon2 import PasswordHasher
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from pisec_server.api.models.paginated.generic import PaginatedParams, PaginatedResponse
from pisec_server.api.models.types.user_columns import UserColumns
from pisec_server.api.models.users import UserCreate, UserResponse, UserUpdate
from pisec_server.core.config import settings
from pisec_server.core.exceptions import InvalidDataError, RecordAlreadyExistsError, RecordNotFoundError
from pisec_server.core.security.hashing import generate_hashed_password
from pisec_server.db.db_models import Camera, User
from pisec_server.services.pagination import paginate

type UserFilterFunc = Callable[[Select[User]], Select[User]]


def get_user(db: Session, user_id_or_email: int | str) -> User | None:
    """Automatically chooses between getting a user by ID or email."""
    if isinstance(user_id_or_email, int):
        return get_user_by_id(db, user_id_or_email)
    else:
        return get_user_by_email(db, user_id_or_email)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Queries the database to get a user using the given ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Queries the database to get a user using the given email address."""
    return db.query(User).filter(User.email == email).first()


def get_users(
    db: Session,
    user_ids: list[int] | None = None,
    email: str | None = None,
    camera_ids: list[int] | None = None,
    skip: int = 0,
    limit: int = 100,
    order_by: UserColumns = UserColumns.ID,
    ascending: bool = True,
    with_filter: UserFilterFunc | None = None,
) -> PaginatedResponse[UserResponse]:
    """Queries and returns a list of all users with pagination.

    If a list of IDs/emails were given, it will only return the given users (if they were found).
    Otherwise, it returns all users in the database (with pagination of course).
    """
    query = select(User)
    if user_ids:
        query = query.where(User.id.in_(user_ids))
    if email:
        query = query.where(User.email.ilike(f"%{email}%"))
    if camera_ids:
        query = query.where(User.cameras.any(Camera.id.in_(camera_ids)))

    if with_filter is not None:
        query = with_filter(query)

    order_condition = User.get_column(order_by).asc() if ascending else User.get_column(order_by).desc()
    query = query.order_by(order_condition)

    params = PaginatedParams(page_index=skip // limit, page_size=limit)
    return paginate(db, query, params, User.to_response)


def create_user(db: Session, user: UserCreate) -> User:
    """Creates a new user using the given inputs.

    The first registered user will automatically be made an admin if `ENABLE_FIRST_USER_ADMIN` env variable is True.
    """
    is_first_user = db.query(User).count() == 0
    is_admin = is_first_user and settings.ENABLE_FIRST_USER_ADMIN

    # check if user with given email already exists
    db_user: User | None = get_user_by_email(db, user.email)
    if db_user:
        raise RecordAlreadyExistsError(f"User with email {user.email} already exists!")

    db_user = User(
        email=user.email, password_hash=generate_hashed_password(user.password, PasswordHasher()), is_admin=is_admin
    )

    db.add(db_user)
    db.flush()
    db.refresh(db_user)

    return db_user


def update_user(db: Session, user_id: int, user: UserUpdate) -> User:
    """Modifies a given user's parameters (excluding ID) via a given ID or email."""
    db_user: User | None = get_user(db, user_id)

    # skip modifying the database if inputs are empty or if user doesn't exist
    if not user.model_fields_set:
        raise InvalidDataError("No data was provided!")

    if not db_user:
        raise RecordNotFoundError(f"User {user_id} does not exist!")

    user_as_dict = user.model_dump(exclude_unset=True)
    if user.password:
        user_as_dict["password_hash"] = generate_hashed_password(user.password, PasswordHasher())

    for key, value in user_as_dict.items():  # pyright: ignore[reportAny]
        if key == "password":  # skip password key as it doesn't exist in User table (uses password_hash instead)
            continue
        setattr(db_user, key, value)

    db.flush()
    db.refresh(db_user)

    return db_user


def delete_user(db: Session, user_id: int) -> User:
    """Deletes a given user via ID or email."""
    db_user: User | None = get_user(db, user_id)

    if not db_user:
        raise RecordNotFoundError(f"User {user_id} does not exist!")

    db.delete(db_user)

    return db_user
