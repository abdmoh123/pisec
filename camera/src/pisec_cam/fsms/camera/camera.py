"""The camera finite state machine class."""

import time

from pisec_cam.core.state_machine import StateMachine
from pisec_cam.fsms.camera.data import CameraCtx
from pisec_cam.fsms.camera.types import CameraEvent, CameraState
from pisec_cam.services.file_name_generator import generate_timestamp_video_name

camera_fsm: StateMachine[CameraState, CameraEvent, CameraCtx] = StateMachine(
    CameraEvent.STOP
)


def _motion_detect_guard(context: CameraCtx) -> bool:
    return context.motion_detector.detect_motion(
        context.settings.detect_delta_ms
    )


@camera_fsm.transition(
    CameraState.DETECTING,
    CameraState.RECORDING,
    CameraEvent.RECORD,
    _motion_detect_guard,
)
def _record_action(context: CameraCtx) -> None:
    context.data = context.camera.start_recording(
        context.settings.video_length_s
    )


@camera_fsm.transition(
    CameraState.DETECTING,
    CameraState.DETECTING,
    CameraEvent.RECORD,
)
def _skip_record_action(_: CameraCtx) -> None:
    print("Motion not detected, skipping recording...")


@camera_fsm.transition(
    CameraState.RECORDING, CameraState.SAVING, CameraEvent.SAVE
)
def _save_action(context: CameraCtx) -> None:
    if not context.data:
        raise ValueError("No data to save")

    context.file_manager.save_data(
        context.data, generate_timestamp_video_name, context.serializer
    )
    context.data = None


@camera_fsm.transition(
    (CameraState.DETECTING, CameraState.SAVING),
    CameraState.SLEEPING,
    CameraEvent.SLEEP,
)
def _sleep_action(context: CameraCtx) -> None:
    print(f"Sleeping for {context.settings.wait_time_ms // 1000} seconds...")
    time.sleep(context.settings.wait_time_ms // 1000)


@camera_fsm.transition(
    CameraState.SLEEPING, CameraState.DETECTING, CameraEvent.WAKE
)
def _wake_action(context: CameraCtx) -> None:  # pyright: ignore[reportUnusedParameter]
    print("Waking up...")


@camera_fsm.transition(
    (
        CameraState.DETECTING,
        CameraState.RECORDING,
        CameraState.SAVING,
        CameraState.SLEEPING,
    ),
    CameraState.STOPPED,
    CameraEvent.STOP,
)
def _shutdown(context: CameraCtx) -> None:
    if context.error:
        print(f"Error has occured: {context.error}")
    print("Shutting down...")
    context.camera.disable()
