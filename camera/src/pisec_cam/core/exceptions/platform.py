"""Exceptions relating to system platform."""


class UnsupportedPlatformError(Exception):
    """Raised when a specific platform isn't supported."""

    def __init__(self, platform: str, message: str) -> None:
        """Constructor for platform error."""
        super().__init__(f"Unsupported platform [{platform}]: {message}")
        self.platform: str = platform
