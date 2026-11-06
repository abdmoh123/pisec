"""Dummy fake camera for testing."""

from collections.abc import Generator
from dataclasses import dataclass
from types import TracebackType
from typing import Self

import numpy as np
from cv2.typing import MatLike

_black_frame: MatLike = np.zeros((480, 640, 3), dtype=np.uint8)
_white_frame: MatLike = np.full((480, 640, 3), 255, dtype=np.uint8)


@dataclass
class DummyCamera:
    """Fake camera for testing purposes."""

    _frame_count: int = 0

    is_enabled: bool = False

    def __enter__(self) -> Self:
        """Method for use with the 'with' statement."""
        self.enable()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Releases the camera."""
        self.disable()

    def _frames(self) -> Generator[MatLike]:
        """A generator simulating a stream of frames from of a camera.

        Every 9 frames, the camera will swap between black and white.
        That way, we can do some motion detection still.

        Decided to use an odd number so the frame difference motion detector can
        see 2 frames with different values.

        Yields:
            The current frame from the camera at the time of the function call.
        """
        while True:
            frame = _black_frame
            frame_type = "BLACK"

            if self._frame_count >= 19:
                self._frame_count = 0

            if self._frame_count >= 9:
                frame = _white_frame
                frame_type = "WHITE"

            print(f"{frame_type=} {self._frame_count=}")
            self._frame_count += 1
            yield frame

    def capture_frame(self) -> MatLike:
        """Captures the current frame from the fake camera.

        Every 10 frames, the camera will return a white frame. Otherwise, it
        will return a black frame.

        Returns:
            The current frame from the camera at the time of the function call.

        Raises:
            RuntimeError: If the fake camera is not enabled.
        """
        if not self.is_enabled:
            raise RuntimeError("Camera is not enabled")

        return next(self._frames())

    def start_recording(self, time_s: int = 600) -> list[MatLike]:
        """Starts the camera recording routine.

        Args:
            time_s: The number of seconds to record, defaults to 600s (10mins).

        Returns:
            A list of frames captured during the recording.

        Raises:
            RuntimeError: If the fake camera is not enabled.
        """
        if not self.is_enabled:
            raise RuntimeError("Camera is not enabled")

        frame_rate: int = 24  # fps
        frames_to_capture = int(time_s * frame_rate)

        print(f"Capturing {frames_to_capture} frames")
        frames = [self.capture_frame() for _ in range(frames_to_capture)]
        print(f"Captured {len(frames)} frames")

        return frames

    def enable(self) -> None:
        """Enables the fake camera.

        This is only implemented to make the fake camera's behaviour more
        closely match real implementations (e.g. OpenCVCamera).
        """
        self.is_enabled = True

    def disable(self) -> None:
        """Disables the fake camera.

        This is only implemented to make the fake camera's behaviour more
        closely match real implementations (e.g. OpenCVCamera).
        """
        self.is_enabled = False
