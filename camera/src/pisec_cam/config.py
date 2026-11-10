"""Stores configs or settings for the app."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from pisec_cam.core.exceptions.platform import UnsupportedPlatformError
from pisec_cam.core.types.camera_type import CameraType
from pisec_cam.core.types.loop_policy_type import LoopPolicyType


def get_default_data_dir() -> Path:
    """Function for getting the default path for the app's config directory.

    Returns:
        The path to the application's default config/data directory.

    Raises:
        UnsupportedPlatformError: When not using posix or windows systems.
    """
    match os.name:
        case "posix":
            return Path.home() / Path(".config/pisec-cam")
        case "nt":
            return Path.home() / Path("AppData/Local/pisec-cam")
        case _:
            raise UnsupportedPlatformError(
                platform=os.name, message="Unable to get default data directory"
            )


@dataclass(frozen=True)
class Settings:
    """Stores configs or settings for the app.

    Attributes:
        data_dir: Directory path to where the app's config/data is stored.
            Defaults to ~/.config/pisec-cam or AppData/Local/Roaming/pisec-cam.
        camera_type: Camera implementation to use.
            Defaults to OpenCV camera type.
        opencv_camera_id: Camera ID to use when using OpenCV camera type.
            Defaults to 0.
        loop_policy_type: What kind of main loop to use.
            Defaults to uploading to an API.
        video_dir: Directory path where recorded videos are stored.
            Derived from data_dir (<data_dir>/recordings).
        photo_dir: Directory path where photos are stored
            Derived from data_dir (<data_dir>/photos).
    """

    data_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("DATA_DIR", str(get_default_data_dir()))
        )
    )

    camera_type: CameraType = field(
        default_factory=lambda: CameraType(
            os.environ.get("CAMERA_TYPE", "opencv")
        )
    )

    opencv_camera_id: int = field(
        default_factory=lambda: int(os.environ.get("OPENCV_CAMERA_ID") or 0)
    )

    loop_policy_type: LoopPolicyType = field(
        default_factory=lambda: LoopPolicyType(
            os.environ.get("LOOP_POLICY_TYPE", "api")
        )
    )

    @property
    def video_dir(self) -> Path:
        """Directory the camera's recordings are stored in."""
        return self.data_dir / "recordings"

    @property
    def photo_dir(self) -> Path:
        """Directory the camera's photos are stored in."""
        return self.data_dir / "photos"


settings = Settings()
