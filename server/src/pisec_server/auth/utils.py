"""Functions related to handling jwts."""

import jwt

from pisec_server.auth.models import TokenHeader, TokenPayload
from pisec_server.core.config import settings


def encode_token(header: TokenHeader, payload: TokenPayload, secret: str = settings.SECRET_KEY) -> str:
    """Encodes a token payload into a JWT using pydantic models."""
    return jwt.encode(payload=payload.model_dump(), key=secret, algorithm=header.alg, headers=header.model_dump())  # pyright: ignore[reportUnknownMemberType]


def decode_token(
    token: str, secret: str = settings.SECRET_KEY, algorithm: str = settings.JWT_ALGORITHM
) -> TokenPayload:
    """Decodes a jwt to a pydantic model of a token payload."""
    payload = jwt.decode(token, secret, algorithms=[algorithm])  # pyright: ignore[reportUnknownMemberType]
    return TokenPayload(sub=payload["sub"], sub_type=payload["sub_type"], exp=payload["exp"], iat=payload["iat"])  # pyright: ignore[reportAny]
