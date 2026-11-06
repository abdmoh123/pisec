"""Module for generating file names."""

import datetime
from collections.abc import Callable

__timestamp_format: str = "%Y-%m-%d_%H-%M-%S"

type FileNameGenerator = Callable[[], str]


def generate_timestamp_video_name(file_ext: str = "mp4") -> str:
    """Generates a timestamped video name.

    Args:
        file_ext: The file extension to use. Defaults to "mp4".

    Returns:
        The timestamped video name.
    """
    current_ts: str = datetime.datetime.now().strftime(__timestamp_format)
    return f"video-{current_ts}.{file_ext}"


def generate_timestamp_photo_name(file_ext: str = "jpg") -> str:
    """Generates a timestamped video name.

    Args:
        file_ext: The file extension to use. Defaults to "jpg".

    Returns:
        The timestamped photo name.
    """
    current_ts: str = datetime.datetime.now().strftime(__timestamp_format)
    return f"photo-{current_ts}.{file_ext}"
