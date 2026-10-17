"""Module containing CRUD functions related to authentication and token management."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from pisec_server.auth.exceptions import TokenDecodingError, TokenEncodingError
from pisec_server.auth.models import TokenHeader, TokenPayload, TokenPayloadCreate, TokenSubjectType
from pisec_server.auth.utils import decode_token, encode_token
from pisec_server.core.config import settings
from pisec_server.db.db_models import RefreshToken


def create_refresh_token(db: Session, user_id: int, expires_at: datetime | None = None) -> RefreshToken:
    """Creates and stores a new refresh token for a user.

    The expiry datetime can be defined in advance to allow rotation of refresh tokens.
    This should only be used for normal users and not for a camera user.
    """
    # Allows rotation of refresh tokens (better security)
    if expires_at is None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Generate a random string for the refresh token, or a JWT for specific needs
    # For simplicity, let's generate a JWT for the refresh token as well
    # NOTE: This assumes that the user is a normal user
    issued_at = datetime.now(timezone.utc)
    refresh_token = encode_token(
        TokenHeader(alg=settings.JWT_ALGORITHM),
        TokenPayload(sub=str(user_id), sub_type=TokenSubjectType.USER, exp=expires_at, iat=issued_at),
        secret=settings.SECRET_KEY,
    )

    db_refresh_token = RefreshToken(token=refresh_token, user_id=user_id, expires_at=expires_at, issued_at=issued_at)
    db.add(db_refresh_token)
    db.flush()
    db.refresh(db_refresh_token)
    return db_refresh_token


def get_refresh_token(db: Session, token: str) -> RefreshToken | None:
    """Retrieves a refresh token from the database."""
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if db_token:
        db_token.expires_at = db_token.expires_at.replace(tzinfo=timezone.utc)
    return db_token


def revoke_refresh_token(db: Session, refresh_token: RefreshToken) -> RefreshToken:
    """Revokes a single refresh token by deleting it from the database."""
    db.delete(refresh_token)

    return refresh_token


def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> list[RefreshToken]:
    """Revokes all refresh tokens for a given user."""
    refresh_tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
    for token in refresh_tokens:
        db.delete(token)

    return refresh_tokens


def clear_expired_refresh_tokens(db: Session, user_id: int) -> None:
    """Clears all expired tokens a user has."""
    query = delete(RefreshToken).where(
        RefreshToken.user_id == user_id, RefreshToken.expires_at < datetime.now(timezone.utc)
    )

    _ = db.execute(query)


def create_personal_access_token(
    client_id: int, subject_type: TokenSubjectType, expires_delta: timedelta | None = None
) -> str:
    """Creates a long-lived or permanent personal access token (PAT)."""
    # PATs are essentially long-lived access tokens. No refresh token associated.
    # The expiration is handled directly in the JWT.
    # NOTE: The ID may be for a regular user or a camera user.
    return create_access_token(
        payload=TokenPayloadCreate(sub=str(client_id), sub_type=subject_type), expires_delta=expires_delta
    )


def create_access_token(payload: TokenPayloadCreate, expires_delta: timedelta | None = None) -> str:
    """Creates a new JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = TokenPayload(sub=payload.sub, sub_type=payload.sub_type, exp=expire, iat=datetime.now(timezone.utc))
    try:
        return encode_token(TokenHeader(alg=settings.JWT_ALGORITHM), to_encode)
    # TODO: Find out what exceptions PyJWT actually raises (docs seem wrong)
    except Exception as e:
        raise TokenEncodingError("Could not create access token") from e


def decode_access_token(token: str) -> TokenPayload:
    """Decodes a JWT access token and returns its payload."""
    try:
        return decode_token(token)
    # TODO: Find out what exceptions PyJWT actually raises (docs seem wrong)
    except Exception as e:
        raise TokenDecodingError("Could not validate credentials") from e
