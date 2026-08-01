"""Custom exception hierarchy for Process Subsystem (Phase 11.4)."""


class ProcessException(Exception):
    """Base exception for Process Runtime errors."""

    def __init__(self, message: str, process_id: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.process_id = process_id


class ProcessNotFoundError(ProcessException):
    """Raised when a process PID or name is not found."""

    pass


class ProcessTerminationError(ProcessException):
    """Raised when a process termination request fails."""

    pass


class ProcessPermissionError(ProcessException):
    """Raised when permissions are insufficient to inspect or control a process."""

    pass


class ProcessTimeoutError(ProcessException):
    """Raised when waiting for process exit times out."""

    pass
