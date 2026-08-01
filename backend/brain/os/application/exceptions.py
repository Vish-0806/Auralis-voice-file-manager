"""Custom exception hierarchy for Application Subsystem (Phase 11.3)."""


class ApplicationException(Exception):
    """Base exception for Application Runtime errors."""

    def __init__(self, message: str, app_id: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.app_id = app_id


class ApplicationNotFoundError(ApplicationException):
    """Raised when an application is not registered or found on system."""

    pass


class ApplicationLaunchError(ApplicationException):
    """Raised when an application fails to launch."""

    pass


class ApplicationRegistryError(ApplicationException):
    """Raised when an application registration or lookup fails."""

    pass


class ApplicationExecutionError(ApplicationException):
    """Raised when an application execution constraint is violated."""

    pass
