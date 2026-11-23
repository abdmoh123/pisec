"""Settings to configure given video stream."""

from dataclasses import dataclass

from pisec_cam.core.types.video_codec import VideoCodec


@dataclass(frozen=True)
class StreamSettings:
    """Properties of a stream that can be configured.

    Attributes:
        duration: Length of the video in seconds.
        codec: The video codec data is stored in. Defaults to H264.
        bitrate: Bitrate of the video. Defaults to 10mbps.
    """

    duration_s: float  # In seconds
    codec: VideoCodec = VideoCodec.H264
    bitrate: int = 10_000_000
