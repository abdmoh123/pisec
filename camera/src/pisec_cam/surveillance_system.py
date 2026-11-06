"""A state machine implementation for the motion detection system."""

from collections.abc import Generator
from dataclasses import dataclass
from typing import ClassVar

from pisec_cam.fsms.camera.camera import camera_fsm
from pisec_cam.fsms.camera.data import CameraCtx
from pisec_cam.fsms.camera.types import CameraEvent, CameraState


@dataclass
class SurveillanceSystem:
    """A camera surveillance system using the state machine pattern.

    Attributes:
        context: The context/data of the camera system.
        state: The current state of the camera system. Defaults to DETECTING.
    """

    context: CameraCtx
    state: CameraState = CameraState.DETECTING

    _event_loop: ClassVar[tuple[CameraEvent, ...]] = (
        CameraEvent.RECORD,
        CameraEvent.SAVE,
        CameraEvent.SLEEP,
        CameraEvent.WAKE,
    )
    # Don't run the save event if the camera is in the detect state
    # As no data has been recorded
    _skip_transitions: ClassVar[list[tuple[CameraState, CameraEvent]]] = [
        (CameraState.DETECTING, CameraEvent.SAVE)
    ]

    def events(self) -> Generator[CameraEvent]:
        """Iterates through the event loop of the camera system."""
        while True:
            for event in SurveillanceSystem._event_loop:
                if (self.state, event) in SurveillanceSystem._skip_transitions:
                    continue
                yield event

    def handle_event(self, event: CameraEvent) -> None:
        """Handles an event and updates the camera system state.

        Args:
            event: The event to handle.
        """
        self.state = camera_fsm.handle_event(self.state, event, self.context)
