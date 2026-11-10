"""Custom exceptions for authentication and authorization."""


class TokenEncodingError(Exception):
    """Exception raised when there is an error encoding the access token."""



class TokenDecodingError(Exception):
    """Exception raised when there is an error decoding the access token."""

