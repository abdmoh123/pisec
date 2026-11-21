"""Protocol for camera implementations."""

from types import TracebackType
from typing import Protocol, Self

from cv2.typing import MatLike


class Camera(Protocol):
    """Generic camera protocol."""

    def __enter__(self) -> Self:
        """Can be used to create a camera."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Releases the camera."""
        ...

    def capture_frame(self) -> MatLike:
        """Captures the current frame from the camera.

        Returns:
            The current frame from the camera at the time of the function call.
        """
        ...

    def start_recording(self, time_s: float = 600) -> list[MatLike]:
        """Starts the camera recording routine.

        Args:
            time_s: The number of seconds to record, defaults to 600s (10mins).

        Returns:
            A list of frames captured during the recording.
        """
        ...

    def enable(self) -> None:
        """Enables the camera."""
        ...

    def disable(self) -> None:
        """Disables the camera."""
        ...
