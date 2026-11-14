"""Module handling video download tokens."""

import secrets
from datetime import UTC, datetime, timedelta

from pisec_server.core.config import settings
from pisec_server.core.models.video_token import DecodedVideoTokenPayload, VideoTokenRecord
from pisec_server.services import hmac_encoder


def generate_signed_download_token(video_id: int, user_id: int) -> VideoTokenRecord:
    """Generates a signed download token for a video.

    Args:
        video_id: The ID of the video to download.
        user_id: The ID of the user downloading the video.

    Returns:
        A VideoTokenRecord containing the nonce, encoded token, and expiration date.
    """
    # Used to identify the temporary token
    nonce: str = secrets.token_urlsafe(16)

    expires_at = datetime.now(UTC) + timedelta(minutes=settings.VIDEO_TOKEN_EXPIRE_MINUTES)

    payload = DecodedVideoTokenPayload(user_id, video_id, expires_at, nonce)

    token = payload.encode()

    return VideoTokenRecord(nonce, token, expires_at)


def extract_payload(payload_str: str) -> DecodedVideoTokenPayload:
    """Extracts the user_id, video_id, expires_at, and nonce from a token payload.

    Args:
        payload_str: The payload string to extract from.

    Returns:
        A tuple containing the user_id, video_id, expires_at, and nonce.

    Raises:
        ValueError: If the payload is malformed (incorrect types).
    """
    user_id_str, video_id_str, expires_at_str, nonce = payload_str.split("|")
    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        return DecodedVideoTokenPayload(int(user_id_str), int(video_id_str), expires_at, nonce)
    except Exception:  # noqa: BLE001
        raise ValueError("Malformed payload")


def decode_signed_download_token(token: str) -> DecodedVideoTokenPayload:
    """Returns user_id if valid. Raises ValueError on any failure.

    Args:
        token: The video download token to decode.

    Returns:
        The payload string decoded into a DecodedVideoTokenPayload.

    Raises:
        ValueError: If the token is malformed or signature is invalid.
    """
    return extract_payload(hmac_encoder.decode(token))


def assert_token_validity(token_payload: DecodedVideoTokenPayload, video_id: int) -> None:
    """Checks if the given token is valid or not."""
    if token_payload.video_id != video_id:
        raise ValueError("Token not valid for this video")

    if token_payload.expires_at < datetime.now(UTC):
        raise ValueError("Token expired")
