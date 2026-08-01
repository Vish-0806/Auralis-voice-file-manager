"""Custom exception hierarchy for Desktop Subsystem (Phase 11.5)."""


class DesktopException(Exception):
    """Base exception for Desktop Subsystem errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ClipboardError(DesktopException):
    """Raised when clipboard read, write, or clear operations fail."""

    pass


class NotificationError(DesktopException):
    """Raised when desktop notification creation or dispatch fails."""

    pass


class DesktopServiceError(DesktopException):
    """Raised when desktop environment or known folder resolution fails."""

    pass
