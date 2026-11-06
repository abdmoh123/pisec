"""Exceptions related to the state machine."""


class TransitionError(KeyError):
    """Exception raised when a transition is invalid."""
