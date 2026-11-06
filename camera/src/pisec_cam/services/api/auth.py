"""Authenticator class inheriting httpx.Auth."""

from collections.abc import Generator
from typing import override

import httpx2
from httpx2 import Request, Response

from pisec_cam.core.models.credential import Credential


class OAuth2Authenticator(httpx2.Auth):
    """Authenticator class inheriting httpx2.Auth."""

    def __init__(
        self, token_url: str, credential: Credential, max_retries: int = 3
    ) -> None:
        """Constructor for the OAuth2Authenticator class.

        Args:
            token_url: The URL to get the token from.
            credential: The credential to use to get the token.
            max_retries: The maximum number of retries to get the token.
        """
        self.token_url: str = token_url
        self.credential: Credential = credential
        self._access_token: str | None = None
        self._max_auth_retries: int = max_retries

    @override
    def auth_flow(self, request: Request) -> Generator[Request, Response]:
        if self._access_token is None:
            token_response = yield self._build_token_request()
            _ = token_response.read()
            _ = token_response.raise_for_status()
            self._access_token = token_response.json()["access_token"]

        # Keep retrying to authenticate until it works out (with a limit)
        for attempt in range(1, self._max_auth_retries + 1):
            request.headers["Authorization"] = f"Bearer {self._access_token}"
            response = yield request

            if response.status_code != 401:
                return

            if attempt == self._max_auth_retries:
                raise RuntimeError(
                    f"Error 401: Failed to authenticate {attempt} times!"
                )

            print(
                "[Auth]: Received 401 error, retrying... "
                + f"({attempt}/{self._max_auth_retries})"
            )
            token_response = yield self._build_token_request()
            _ = token_response.read()
            _ = token_response.raise_for_status()
            self._access_token = token_response.json()["access_token"]

    def _build_token_request(self) -> Request:
        return httpx2.Request(
            method="POST",
            url=self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.credential.client_id,
                "client_secret": self.credential.client_secret,
            },
        )
