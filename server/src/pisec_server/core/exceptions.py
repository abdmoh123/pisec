"""Custom exceptions for the server."""


class RecordNotFoundError(Exception):
    """Exception raised when a record is not found."""



class RecordAlreadyExistsError(Exception):
    """Exception raised when a record already exists."""



class InvalidDataError(Exception):
    """Exception raised when invalid data is provided."""



class InvalidFileNameError(Exception):
    """Exception raised when a file name is not valid."""

