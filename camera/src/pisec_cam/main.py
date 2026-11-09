"""Main endpoint of the application."""

from pathlib import Path

import typer

from pisec_cam.config import settings
from pisec_cam.core.cameras.opencv_camera import OpenCVCamera
from pisec_cam.core.serializers.opencv_serializer import OpenCVSerializer
from pisec_cam.core.types.loop_policy_type import LoopPolicyType
from pisec_cam.fsms.camera.data import CameraCtx, CameraSettings
from pisec_cam.services.camera_service import CameraService
from pisec_cam.services.data_setup_service import (
    setup_system,
)
from pisec_cam.services.factories.camera_factory import create_camera
from pisec_cam.services.factories.loop_policy_factory import create_loop_policy
from pisec_cam.services.file_manager import FileManager
from pisec_cam.services.motion.frame_difference_detector import (
    CV2FrameDifferenceDetectorService,
)
from pisec_cam.surveillance_system import SurveillanceSystem

app = typer.Typer()


@app.command()
def serve(
    wait_time_ms: int = 1000,
    delta_ms: int = 500,
    video_length_s: int = 10,
    video_dir: str | None = None,
    max_files: int = 5,
) -> None:
    """Runs the motion detection service.

    Args:
        wait_time_ms: The number of milliseconds to sleep between checks.
            Defaults to 1000ms (1s).
        delta_ms: The number of milliseconds to wait between frames.
            Defaults to 500ms (0.5s).
        video_length_s: The number of seconds to record a video.
            Defaults to 10s.
        video_dir: An override for the directory (string) to save the video to.
            Defaults to the environment variable value (<data_dir>/recordings).
        max_files: The maximum number of files to keep in the directory.
            Defaults to 5 files.
    """
    # Prepare things before starting the FSM
    env_video_dir = settings.video_dir
    video_dir_path = Path(video_dir or env_video_dir).resolve()
    video_dir_path.mkdir(parents=True, exist_ok=True)

    # Ensure all the required data for using the API exists
    loop_policy_type = settings.loop_policy_type
    if loop_policy_type is LoopPolicyType.API:
        _ = setup_system()

    # Context manager as safety-net in case FSM fails to cleanup on STOP event
    with create_camera(settings.camera_type) as camera:
        motion_detector = CV2FrameDifferenceDetectorService(camera)
        file_manager = FileManager(video_dir_path, max_files)
        serializer = OpenCVSerializer()

        camera_fsm = SurveillanceSystem(
            CameraCtx(
                camera,
                motion_detector,
                file_manager,
                serializer,
                CameraSettings(wait_time_ms, delta_ms, video_length_s),
            )
        )

        loop_policy = create_loop_policy(loop_policy_type, camera_fsm)
        loop_policy.run_loop()

        raise typer.Exit(1 if loop_policy.camera_system.context.error else 0)


@app.command()
def record(
    seconds: int = 600,
    video_dir: str | None = None,
    opencv_cam_id: int | None = None,
) -> None:
    """Starts the camera recording routine.

    Args:
        seconds: The number of seconds to record.
            Defaults to 600s (10mins).
        video_dir: An override for the directory (string) to save the video to.
            Defaults to the environment variable value (<data_dir>/recordings).
        opencv_cam_id: An override for the camera ID to pass into opencv.
            Defaults to the environment variable (0 by default).
    """
    env_video_dir = settings.video_dir
    video_dir_path = Path(video_dir or env_video_dir).resolve()
    video_dir_path.mkdir(parents=True, exist_ok=True)

    camera_id = opencv_cam_id or settings.opencv_camera_id

    with OpenCVCamera(camera_id) as camera:
        # Negative max_files disables the check
        file_manager = FileManager(video_dir_path, max_files=-1)
        serializer = OpenCVSerializer()
        camera_service = CameraService(camera, serializer, file_manager)
        camera_service.record_video(seconds)


@app.command()
def shoot(
    photo_dir: str | None = None, opencv_cam_id: int | None = None
) -> None:
    """Captures the current frame from the camera.

    Args:
        photo_dir: An override for the directory (string) to save the photo to.
            Defaults to the environment variable value (<data_dir>/photos).
        opencv_cam_id: An override for the camera ID to pass into opencv.
            Defaults to the environment variable (0 by default).
    """
    env_photo_dir = settings.photo_dir
    photo_dir_path = Path(photo_dir or env_photo_dir).resolve()
    photo_dir_path.mkdir(parents=True, exist_ok=True)

    camera_id = opencv_cam_id or settings.opencv_camera_id

    with OpenCVCamera(camera_id) as camera:
        # Negative max_files disables the check
        file_manager = FileManager(photo_dir_path, max_files=-1)
        serializer = OpenCVSerializer()
        camera_service = CameraService(camera, serializer, file_manager)
        camera_service.take_photo()


@app.command()
def setup() -> None:
    """Sets up data for the application."""
    changed = setup_system()
    if not changed:
        print("All data is already set up!")


if __name__ == "__main__":
    app()
