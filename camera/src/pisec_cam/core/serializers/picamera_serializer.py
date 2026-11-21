"""Serializer implementation using picamera2."""

from pathlib import Path

from cv2.typing import MatLike
from picamera2 import Picamera2  # pyright: ignore[reportMissingTypeStubs]

from pisec_cam.core.cameras.picamera import PiCamera
from pisec_cam.core.serializers.opencv_serializer import OpenCVSerializer
from pisec_cam.core.serializers.serializer import Serializer


class PiCameraSerializer:
    """picamera2-based implementation for the Serializer protocol."""

    def __init__(self, camera: PiCamera) -> None:
        """Creates a picamera2-based serialiser.

        Args:
            camera: A PiCamera instance.
        """
        self._camera: Picamera2 = camera.camera
        self._opencv_serializer: Serializer = OpenCVSerializer(camera.fps)

    def write_video(self, data: list[MatLike], file_path: Path) -> None:
        """Writes video data to a file.

        Just uses openCV as picamera2 doesn't serialise arrays of data.

        Args:
            data: The video data to write.
            file_path: The path to write the video to.
        """
        self._opencv_serializer.write_video(data, file_path)

    def write_image(self, data: MatLike, file_path: Path) -> None:
        """Writes image data to a file.

        Just uses openCV as picamera2 doesn't serialise arrays of data.

        Args:
            data: The image data to write.
            file_path: The path to write the image to.
        """
        self._opencv_serializer.write_image(data, file_path)
