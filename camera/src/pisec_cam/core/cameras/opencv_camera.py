"""Generic camera implementation using opencv."""

import time
from dataclasses import dataclass
from types import TracebackType
from typing import Self

import cv2
from cv2.typing import MatLike


@dataclass
class OpenCVCamera:
    """Generic camera implementation using opencv.

    Attributes:
        camera: The internal camera object used by the class. For usability's
            sake, the field is exposed publicly.
    """

    _camera_id: int
    camera: cv2.VideoCapture | None = None

    def __init__(self, camera_id: int = 0) -> None:
        """Initializes the camera.

        Args:
            camera_id: The internal id of the camera to use, defaults to 0 (main
              camera).
        """
        self._camera_id = camera_id
        self.enable()

    def __enter__(self) -> Self:
        """Method for use with the 'with' statement."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Releases the camera."""
        self.disable()

    def capture_frame(self) -> MatLike:
        """Captures the current frame from the camera.

        Returns:
            The current frame from the camera at the time of the function call.
        """
        if self.camera is None:
            raise RuntimeError("Camera is not enabled")

        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture frame")
        return frame

    def start_recording(self, time_s: float = 600) -> list[MatLike]:
        """Starts the camera recording routine.

        Args:
            time_s: The number of seconds to record, defaults to 600s (10mins).

        Returns:
            A list of frames captured during the recording.
        """
        if self.camera is None:
            raise RuntimeError("Camera is not enabled")

        frame_rate: int = 24  # fps
        frame_time: float = 1.0 / frame_rate

        frames: list[MatLike] = []
        frames_to_capture = int(time_s * frame_rate)
        print(f"Capturing {frames_to_capture} frames")
        for i in range(frames_to_capture):
            start_time: float = time.time()
            ret, frame = self.camera.read()

            # If the frame couldn't be captured, break early
            if not ret:
                break

            frames.append(frame)
            end_time: float = time.time()
            time_taken = end_time - start_time
            # Ensure sleep time isn't negative
            time.sleep(max(0, frame_time - time_taken))
            print(
                f"Time taken/frame time: {time_taken}/{frame_time} seconds",
                f"\nframe: {i}/{frames_to_capture}",
            )
        print(f"Captured {len(frames)} frames")

        return frames

    def enable(self) -> None:
        """Enables the camera."""
        if self.camera is not None:
            print("Camera already enabled")
            return

        self.camera = cv2.VideoCapture(self._camera_id)
        if not self.camera.isOpened():
            self.disable()
            raise RuntimeError("Failed to open camera")

        print(f"Camera {self._camera_id} enabled")

    def disable(self) -> None:
        """Disables the camera."""
        if self.camera is None:
            print("Camera already disabled")
            return

        if self.camera.isOpened():
            self.camera.release()
            print("Camera released")

        self.camera = None
        print("Camera disabled")
