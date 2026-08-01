"""Custom exception hierarchy for Filesystem Subsystem (Phase 11.2)."""


class FilesystemException(Exception):
    """Base exception for all filesystem runtime errors."""

    def __init__(self, message: str, path: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.path = path


class PermissionDeniedError(FilesystemException):
    """Raised when access permissions are insufficient for requested action."""

    pass


class FileNotFoundError(FilesystemException):
    """Raised when a requested file or directory does not exist."""

    pass


class FileExistsError(FilesystemException):
    """Raised when attempting to create a file or directory that already exists."""

    pass


class DirectoryNotEmptyError(FilesystemException):
    """Raised when attempting to remove or clear a directory that is not empty."""

    pass


class TransactionError(FilesystemException):
    """Raised when a filesystem transaction or rollback fails."""

    pass


class PathSafetyError(FilesystemException):
    """Raised when a path violates safety constraints (e.g. directory traversal)."""

    pass
