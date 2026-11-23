"""Video codecs."""

from enum import StrEnum, auto


class VideoCodec(StrEnum):
    """Types of video codecs."""

    H264 = auto()
    MPEG4 = auto()
