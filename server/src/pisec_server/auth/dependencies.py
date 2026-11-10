"""Module containing functions and dependencies for authentication and authorization."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from pisec_server.auth.exceptions import TokenDecodingError
from pisec_server.auth.models import TokenPayload, TokenSubjectType
from pisec_server.auth.services import decode_access_token
from pisec_server.db.database import get_db
from pisec_server.db.db_models import CameraCredential, User
from pisec_server.services.camera_credential import get_credential
from pisec_server.services.user import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v0/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v0/auth/token", auto_error=False)


def get_current_user(
    db_session: Annotated[Session, Depends(get_db)], token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """Dependency to get the current authenticated user."""
    try:
        payload: TokenPayload = decode_access_token(token)
    except TokenDecodingError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials") from e

    # Shouldn't need to check expiry due to ExpiredSignatureError, but kept just in case
    if payload.exp < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token")

    # Check if the token is for a regular user
    if payload.sub_type != TokenSubjectType.USER:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a user token")

    try:
        user_id: int = int(payload.sub)
    except ValueError:
        raise ValueError("Token subject isn't valid!")

    user: User | None = get_user(db_session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    return user


def get_current_user_optional(
    db_session: Annotated[Session, Depends(get_db)], token: Annotated[str | None, Depends(oauth2_scheme_optional)]
) -> User | None:
    """Dependency to get the current authenticated user.

    Unlike the other function, this returns none if any step failed instead of an error.
    This makes this function worse for error handling but there may be cases where we need to use this.
    """
    if token is None:
        return None

    try:
        payload: TokenPayload = decode_access_token(token)
    except TokenDecodingError:
        return None

    # Shouldn't need to check expiry due to ExpiredSignatureError, but kept just in case
    if payload.exp < datetime.now(UTC):
        return None

    # Check if the token is for a regular user
    if payload.sub_type != TokenSubjectType.USER:
        return None

    try:
        user_id: int = int(payload.sub)
    except ValueError:
        return None

    user: User | None = get_user(db_session, user_id)
    return user


def get_current_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency to get the current authenticated admin user."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user


def get_current_credential(
    db_session: Annotated[Session, Depends(get_db)], token: Annotated[str, Depends(oauth2_scheme)]
) -> CameraCredential:
    """Dependency to get the current authenticated camera user."""
    payload: TokenPayload = decode_access_token(token)

    # Shouldn't need to check expiry due to ExpiredSignatureError, but kept just in case
    if payload.exp < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token")

    # Check if the token is for a camera
    if payload.sub_type != TokenSubjectType.CAMERA:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a camera token")

    try:
        credential_id: str = payload.sub
    except ValueError:
        raise ValueError("Token subject isn't valid!")

    credential: CameraCredential | None = get_credential(db_session, credential_id)
    if credential is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    return credential
