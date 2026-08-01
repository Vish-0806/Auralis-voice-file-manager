"""Custom exception hierarchy for Window Subsystem (Phase 11.6)."""


class WindowException(Exception):
    """Base exception for Window Subsystem errors."""

    def __init__(self, message: str, window_id: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.window_id = window_id


class WindowNotFoundError(WindowException):
    """Raised when a specified window ID or title is not found."""

    pass


class WindowOperationError(WindowException):
    """Raised when a window manipulation operation fails."""

    pass


class WindowPermissionError(WindowException):
    """Raised when permissions are insufficient to manipulate a window."""

    pass
