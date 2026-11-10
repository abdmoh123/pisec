"""A module for signing payloads with HMAC-SHA256."""

import base64
import hashlib
import hmac

from pisec_server.core.config import settings


def sign(payload: str) -> str:
    """Signs a payload with HMAC-SHA256.

    Args:
        payload: The payload to sign.

    Returns:
        The signature of the payload.

    Raises:
        UnicodeEncodeError: If the payload failed to encode.
        UnicodeDecodeError: If the base64 value failed to decode.
    """
    signature = hmac.new(settings.HMAC_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode()


def encode(payload: str) -> str:
    """Encodes a payload with HMAC-SHA256 signature.

    Args:
        payload: The payload to encode.

    Returns:
        The encoded payload with signature.

    Raises:
        UnicodeEncodeError: If the payload failed to encode.
        UnicodeDecodeError: If the base64 value failed to decode.
    """
    signature = sign(payload)

    base64_string = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"{base64_string}.{signature}"


def decode(token: str) -> str:
    """Decodes a token into a payload and validates the signature.

    Args:
        token: The token to decode.

    Returns:
        The decoded payload of the token.

    Raises:
        ValueError: If the token is malformed or signature is invalid.
        UnicodeEncodeError: If the validation failed to encode payload.
        UnicodeDecodeError: If the validation failed to decode the base64 value.
    """
    try:
        encoded_payload, signature = token.rsplit(".", 1)
        padded = encoded_payload + "=" * (-len(encoded_payload) % 4)
        payload = base64.urlsafe_b64decode(padded).decode()
    except Exception:  # noqa: BLE001
        raise ValueError("Malformed token")

    if not is_valid(signature, payload):
        raise ValueError("Invalid signature")

    return payload


def is_valid(actual_signature: str, payload: str) -> bool:
    """Checks if a signature is valid for a payload.

    Args:
        actual_signature: The signature to check the validity of.
        payload: The payload to validate against.

    Returns:
        True if the signature is valid, False otherwise.

    Raises:
        UnicodeEncodeError: If the signing failed to encode payload.
        UnicodeDecodeError: If the signing failed to decode the base64 value.
    """
    expected_signature = sign(payload)
    return hmac.compare_digest(actual_signature, expected_signature)
