"""Pi camera 2 implementation for raspberry pi devices."""

import time
from types import TracebackType
from typing import Any, Self

from cv2.typing import MatLike
from picamera2 import Picamera2  # pyright: ignore[reportMissingTypeStubs]


class PiCamera:
    """picamera2-based implementation for the Camera protocol class."""

    def __init__(
        self, fps: int = 24, width: int = 640, height: int = 480
    ) -> None:
        """Creates a new instance of a PiCamera object.

        Arguments:
            fps: Recording's frames per second. Defaults to 24 fps.
            width: Width in pixels of the images and videos recorded. Defaults
                to 640 pixels.
            height: Height in pixels of the images and videos recorded. Defaults
                to 480 pixels.
        """
        self.camera: Picamera2 = Picamera2()
        self._is_enabled: bool = False

        self._fps: int = fps
        try:
            # RGB888 actually puts it in BGR format that opencv understands
            self._config: dict[str, Any] = (  # pyright: ignore[reportExplicitAny]
                self.camera.create_video_configuration(  # pyright: ignore[reportUnknownMemberType]
                    main={"size": (width, height), "format": "RGB888"},
                    controls={"FrameRate": self._fps},
                )
            )
            self.camera.configure(self._config)  # pyright: ignore[reportUnknownMemberType]
        except BaseException:
            self.camera.close()
            raise

    def __enter__(self) -> Self:
        """Enables/starts the camera when initialising via context manager.

        Returns:
            A new instance of PiCamera.
        """
        self.enable()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Releases the camera when context manager deletes the object."""
        self.disable()
        self.camera.close()

    def capture_frame(self) -> MatLike:
        """Captures the current frame from the camera.

        Returns:
            The current frame from the camera at the time of the function call.

        Raises:
            RuntimeError: When the camera is not enabled.
        """
        if not self.is_enabled:
            raise RuntimeError("Camera is not enabled")

        frame: MatLike = self.camera.capture_array("main")  # pyright: ignore[reportUnknownMemberType]
        return frame

    def start_recording(self, time_s: int = 600) -> list[MatLike]:
        """Starts the camera recording routine.

        Args:
            time_s: The number of seconds to record, defaults to 600s (10mins).

        Returns:
            A list of frames captured during the recording.

        Raises:
            RuntimeError: When the camera is not enabled.
        """
        if not self.is_enabled:
            raise RuntimeError("Camera is not enabled")

        frames: list[MatLike] = []
        time_end = time.monotonic() + time_s
        while time.monotonic() < time_end:
            request = self.camera.capture_request()  # pyright: ignore[reportUnknownMemberType]
            try:
                frames.append(request.make_array("main"))
            finally:
                request.release()
        return frames

    def enable(self) -> None:
        """Enables the camera."""
        if self.is_enabled:
            return

        self.camera.start()  # pyright: ignore[reportUnknownMemberType]
        self._is_enabled = True

    def disable(self) -> None:
        """Disables the camera."""
        if not self.is_enabled:
            return

        try:
            self.camera.stop()
        finally:
            self.camera.close()
        self._is_enabled = False

    @property
    def is_enabled(self) -> bool:
        """Whether or not the camera is enabled.

        Returns:
            True if the camera was enabled and False otherwise.
        """
        return self._is_enabled
