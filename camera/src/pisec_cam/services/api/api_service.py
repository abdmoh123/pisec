"""Service for interacting with the API server."""

from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Self

import httpx2
from httpx2 import ConnectError, Response

from pisec_cam.core.api.api_service_context import APIServiceContext
from pisec_cam.core.models.camera import Camera, CameraCreate, CameraUpdate
from pisec_cam.core.models.user import User


@dataclass
class APIService:
    """Service for interacting with the API server.

    Attributes:
        api_url: The URL of the API server.
        authenticator: The authenticator to use to authenticate with the API
            server.
    """

    context: APIServiceContext

    _client: httpx2.Client = field(init=False)

    def __post_init__(self) -> None:
        """Post init constructor for this API service dataclass."""
        self._client = httpx2.Client(
            base_url=self.context.api_url, auth=self.context.authenticator
        )

    def __enter__(self) -> Self:
        """Context manager entry point."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit point."""
        self._client.close()

    @classmethod
    def is_reachable(cls, api_url: str) -> bool:
        """Checks if the given API server is reachable.

        Args:
            api_url: The URL of the API server.

        Returns:
            True if the API server is reachable, False otherwise.
        """
        try:
            response = httpx2.get(url=api_url)
            return response.status_code == 200
        except ConnectError as e:
            print(f"Failed to connect: {e}")
            return False

    def can_connect(self) -> bool:
        """Checks if the API server is reachable.

        Returns:
            True if the API server is reachable, False otherwise.
        """
        return APIService.is_reachable(self.context.api_url)

    def get_registered_users(
        self, page_index: int, page_size: int
    ) -> list[User]:
        """Returns a list of users subscribed to this camera.

        Args:
            page_index: The index of the page to get.
            page_size: The number of users to get per page.

        Returns:
            A list of users registered to this camera.
        """
        if self.context.authenticator.credential.camera_id is None:
            raise ValueError("Camera ID is not set")

        response: Response = self._client.get(
            url=f"/cameras/{self.context.authenticator.credential.camera_id}/users",
            auth=self.context.authenticator,
            params={"page_index": page_index, "page_size": page_size},
        ).raise_for_status()
        return [User(**user) for user in response.json()]  # pyright: ignore[reportAny]

    def upload_video(self, video_path: Path) -> None:
        """Uploads a video to the API server.

        Args:
            video_path: The path to the video to upload.
        """
        with open(video_path, "rb") as video_file:
            _ = self._client.post(
                url="/videos/",
                auth=self.context.authenticator,
                files={
                    "video_file": (video_path.name, video_file, "video/mp4"),
                    "file_name": (None, video_path.name),
                },
            ).raise_for_status()

    def register_camera(self, camera_details: CameraCreate) -> None:
        """Registers the camera with the server.

        Args:
            camera_details: The details of the camera to register.
        """
        # Don't try to register if registration was already done
        if self.context.authenticator.credential.camera_id is not None:
            camera_id = self.context.authenticator.credential.camera_id
            print(f"Skipped: Camera id={camera_id} already registered")
            return

        response = self._client.post(
            url="/cameras/",
            auth=self.context.authenticator,
            json={
                "name": camera_details.name,
                "mac_address": camera_details.mac_address,
            },
        ).raise_for_status()

        camera = Camera(**response.json())  # pyright: ignore[reportAny]
        # Update the credential camera ID in case we want to use it later
        self.context.authenticator.credential.camera_id = camera.id

    def unregister_camera(self, camera_id: int) -> None:
        """Unregisters the camera from the server.

        Args:
            camera_id: The ID of the camera to unregister.
        """
        _ = self._client.delete(
            url=f"/cameras/{camera_id}",
            auth=self.context.authenticator,
        ).raise_for_status()

        # Reset the credential camera ID back to None
        self.context.authenticator.credential.camera_id = None

    def update_camera(self, camera_data: CameraUpdate) -> None:
        """Updates the camera's data on the server.

        Args:
            camera_data: The data to update the camera with.
        """
        if self.context.authenticator.credential.camera_id is None:
            raise ValueError("Camera ID is not set")

        _ = self._client.put(
            url=f"/cameras/{self.context.authenticator.credential.camera_id}",
            auth=self.context.authenticator,
            json=camera_data.model_dump(),
        ).raise_for_status()
