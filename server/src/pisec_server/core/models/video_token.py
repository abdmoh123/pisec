"""Dataclass grouping token info used for downloading videos."""

from dataclasses import dataclass
from datetime import datetime
from typing import override

from pisec_server.services import hmac_encoder


@dataclass(frozen=True)
class VideoTokenRecord:
    """A struct containing info about a video token.

    This also matches the Nonceable protocol.
    """

    nonce: str
    token: str
    expires_at: datetime


@dataclass(frozen=True)
class DecodedVideoTokenPayload:
    """A struct containing the contents of a video token payload."""

    user_id: int
    video_id: int
    expires_at: datetime
    nonce: str

    @override
    def __str__(self) -> str:
        return f"{self.user_id}|{self.video_id}|{self.expires_at.isoformat()}|{self.nonce}"

    def encode(self) -> str:
        """Encodes itself into a token string.

        Returns:
            An encoded token string.

        Raises:
            UnicodeEncodeError: If the payload failed to encode.
            UnicodeDecodeError: If the base64 value failed to decode.
        """
        return hmac_encoder.encode(str(self))
