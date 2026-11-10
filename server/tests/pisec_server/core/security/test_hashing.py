"""Tests for the hashing module."""

import pytest
from argon2 import PasswordHasher
from argon2.exceptions import HashingError

from pisec_server.core.security.hashing import generate_hashed_password, verify_password


def test_generate_hashed_password() -> None:
    """Test the generate_hashed_password function."""
    ph = PasswordHasher()
    salt: str = "12345678"
    salt_encoding: str = "utf-8"

    test_password: str = "password"
    hashed_password = generate_hashed_password(test_password, ph, salt, salt_encoding)

    hash_without_salt: str = hashed_password.split(":")[1]
    assert ph.verify(hash=hash_without_salt, password=test_password)


def test_generate_hashed_password_short_salt() -> None:
    """Test if the software breaks if the salt is too short."""
    ph = PasswordHasher()
    salt: str = "1234"
    salt_encoding: str = "utf-8"

    test_password: str = "password"

    with pytest.raises(HashingError):
        _ = generate_hashed_password(test_password, ph, salt, salt_encoding)


def test_verify_password_valid() -> None:
    """Test the verify_password function with valid password pairs."""
    ph = PasswordHasher()
    salt: str = "12345678"
    salt_encoding: str = "utf-8"

    test_password: str = "password"
    test_hashed_password: str = generate_hashed_password(test_password, ph, salt, salt_encoding)

    assert verify_password(test_password, test_hashed_password, ph)


def test_verify_password_invalid() -> None:
    """Test the verify_password function with differing password pairs."""
    ph = PasswordHasher()
    salt: str = "12345678"
    salt_encoding: str = "utf-8"

    test_password: str = "password"
    test_hashed_password: str = generate_hashed_password(test_password, ph, salt, salt_encoding)

    wrong_passwords: list[str] = ["1234", "PASSWORD", "abcABC123"]
    assert all(not verify_password(wrong_password, test_hashed_password, ph) for wrong_password in wrong_passwords)
