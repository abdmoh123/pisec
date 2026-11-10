"""Tests for regex patterns."""

import re

import pisec_server.core.validation.regex as regex_patterns


def test_camera_name_regex() -> None:
    """Test the camera name regex."""
    test_camera_names = ["asdf1234", "abc", "a", "camera-1"]
    pattern = re.compile(regex_patterns.camera_name_regex)

    assert all(pattern.match(name) for name in test_camera_names)


def test_email_regex() -> None:
    """Test the email regex pattern against valid emails."""
    test_emails = ["test@example.com", "test@gmail.com", "test@hotmail.com", "test@yahoo.co.uk", "test@protonmail.ch"]

    pattern = re.compile(regex_patterns.email_regex)
    assert all(pattern.match(email) for email in test_emails)
