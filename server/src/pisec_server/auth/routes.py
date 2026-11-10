"""FastAPI routes related to user authentication and authorization."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from pisec_server.auth.dependencies import (
    get_current_user,
)
from pisec_server.auth.exceptions import TokenEncodingError
from pisec_server.auth.models import Token, TokenPayloadCreate, TokenSubjectType
from pisec_server.auth.services import (
    clear_expired_refresh_tokens,
    create_access_token,
    create_personal_access_token,
    create_refresh_token,
    get_refresh_token,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
)
from pisec_server.core.config import settings
from pisec_server.core.security.hashing import verify_password
from pisec_server.db.database import get_db
from pisec_server.db.db_models import User
from pisec_server.services.camera_credential import get_credential
from pisec_server.services.user import get_user_by_email, get_user_by_id  # Import get_user_by_id

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db_session: Annotated[Session, Depends(get_db)]
) -> Token:
    """Authenticates a user and returns an access token and a refresh token."""
    user = get_user_by_email(db_session, form_data.username)
    ph = PasswordHasher()
    if not user or not verify_password(form_data.password, user.password_hash, ph):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Clear any expired refresh tokens to prevent table from infinite growth
    clear_expired_refresh_tokens(db_session, user.id)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    try:
        access_token = create_access_token(
            TokenPayloadCreate(sub=str(user.id), sub_type=TokenSubjectType.USER), expires_delta=access_token_expires
        )
    except TokenEncodingError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    refresh_token = create_refresh_token(db_session, user.id)

    return Token(access_token=access_token, refresh_token=refresh_token.token, token_type="bearer")


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    refresh_token_str: Annotated[str, Form(alias="refresh_token")], db_session: Annotated[Session, Depends(get_db)]
) -> Token:
    """Refreshes an access token using a valid refresh token."""
    refresh_token_db = get_refresh_token(db_session, refresh_token_str)

    if not refresh_token_db or refresh_token_db.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Clear any expired refresh tokens to prevent table from infinite growth
    clear_expired_refresh_tokens(db_session, refresh_token_db.user_id)

    user = get_user_by_id(db_session, refresh_token_db.user_id)  # Use get_user_by_id here
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Create a new refresh token and revoke the old one for rotation
    new_refresh_token = create_refresh_token(db_session, user.id, refresh_token_db.expires_at)
    _ = revoke_refresh_token(db_session, refresh_token_db)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    try:
        new_access_token = create_access_token(
            TokenPayloadCreate(sub=str(user.id), sub_type=TokenSubjectType.USER), expires_delta=access_token_expires
        )
    except TokenEncodingError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return Token(access_token=new_access_token, refresh_token=new_refresh_token.token, token_type="bearer")


# Purposely using a post method to keep the refresh token hidden
@router.post("/refresh/expiry")
def get_refresh_token_expiry(
    refresh_token: Annotated[str, Form()], db_session: Annotated[Session, Depends(get_db)]
) -> datetime:
    """Allows a client to see if their token is expired or invalid."""
    refresh_token_db = get_refresh_token(db_session, refresh_token)

    if not refresh_token_db or refresh_token_db.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return refresh_token_db.expires_at


@router.post("/pat", response_model=Token)
def generate_personal_access_token(
    current_user: Annotated[User, Depends(get_current_user)],
    expires_in_minutes: Annotated[int | None, Form()] = None,
) -> Token:
    """Generates a long-lived personal access token (PAT) that could be used in CLI or for automation purposes.

    Set expires_in_minutes to 0 for a permanent token (warning should exist on frontend).
    """
    if expires_in_minutes is not None and expires_in_minutes < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expires in minutes cannot be negative")

    expires_delta: timedelta | None = None
    if expires_in_minutes == 0:  # Shortcut for a permanent token
        # A very long timedelta effectively makes it permanent for practical purposes within JWT limits
        expires_delta = timedelta(days=365 * 100)  # 100 years
    elif expires_in_minutes is not None:
        expires_delta = timedelta(minutes=expires_in_minutes)

    # If the expires_in_minutes == None, the token will use the default expiry date
    # See settings.ACCESS_TOKEN_EXPIRE_MINUTES
    try:
        pat_token = create_personal_access_token(current_user.id, TokenSubjectType.USER, expires_delta)
    except TokenEncodingError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return Token(access_token=pat_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    refresh_token_str: Annotated[str, Form(alias="refresh_token")],  # Expect refresh token to revoke specific session
    db_session: Annotated[Session, Depends(get_db)],
) -> None:
    """Logs out the current session by revoking the provided refresh token.

    Requires the refresh token to identify the specific session to revoke.
    """
    refresh_token_db = get_refresh_token(db_session, refresh_token_str)

    if not refresh_token_db or refresh_token_db.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token or not owned by user"
        )

    _ = revoke_refresh_token(db_session, refresh_token_db)


@router.post("/logout/all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[Session, Depends(get_db)],
) -> None:
    """Logs out all sessions for the current user by revoking all their refresh tokens."""
    _ = revoke_all_user_refresh_tokens(db_session, current_user.id)


@router.post("/camera_token", response_model=Token)
def login_for_camera_token(
    grant_type: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    client_secret: Annotated[str, Form()],
    db_session: Annotated[Session, Depends(get_db)],
) -> Token:
    """Authenticates a camera and returns an access token."""
    if grant_type != "client_credentials":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_grant_type")

    camera_credential = get_credential(db_session, client_id)
    ph = PasswordHasher()
    if not camera_credential or not verify_password(client_secret, camera_credential.client_secret_hash, ph):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(hours=settings.CAMERA_TOKEN_EXPIRE_HOURS)
    try:
        access_token = create_access_token(
            TokenPayloadCreate(sub=str(camera_credential.client_id), sub_type=TokenSubjectType.CAMERA),
            expires_delta=access_token_expires,
        )
    except TokenEncodingError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return Token(access_token=access_token, token_type="bearer")
