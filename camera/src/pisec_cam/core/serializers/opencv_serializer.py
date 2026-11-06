"""OpenCV based implementation of the Serializer protocol."""

from pathlib import Path

import cv2
from cv2 import (  # type: ignore[attr-defined]
    VideoWriter,
    VideoWriter_fourcc,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]
)
from cv2.typing import MatLike

from pisec_cam.core.exceptions.serialization import SerializationError


class OpenCVSerializer:
    """OpenCV based implementation of the Serializer protocol."""

    def write_video(self, data: list[MatLike], file_path: Path) -> None:
        """OpenCV based implementation of the write_video method.

        Args:
            data: The video data to write.
            file_path: The path to write the video to.

        Raises:
            SerializationError: If the video could not be written.
        """
        out = VideoWriter(
            filename=file_path,
            fourcc=VideoWriter_fourcc(*"mp4v"),  # pyright: ignore[reportUnknownArgumentType]
            fps=24.0,
            frameSize=data[0].shape[1::-1],  # pyright: ignore[reportAny]
        )
        writer_error: Exception | None = None
        try:
            for frame in data:
                _ = out.write(frame)
        except Exception as e:  # noqa: BLE001
            # Prevent any error from raising so it can be converged to
            # SerializationError below
            writer_error = e
        finally:
            # Ensure that the video writer is closed
            out.release()

        if writer_error:
            raise SerializationError(file_path) from writer_error

    def write_image(self, data: MatLike, file_path: Path) -> None:
        """OpenCV based implementation of the write_image method.

        Args:
            data: The image data to write.
            file_path: The path to write the image to.

        Raises:
            SerializationError: If the image could not be written.
        """
        res: bool = cv2.imwrite(file_path, data)
        if not res:
            raise SerializationError(file_path)
