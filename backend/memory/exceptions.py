"""Exceptions for the Auralis memory subsystem."""

from core.exceptions import AuralisException


class MemoryException(AuralisException):
    """Base exception for all Auralis memory errors."""
    pass


class DatabaseConnectionError(MemoryException):
    """Raised when connecting to the database fails."""
    pass


class DataIntegrityError(MemoryException):
    """Raised when a database constraint/integrity violation occurs (e.g. unique constraint)."""
    pass


class RecordNotFoundError(MemoryException):
    """Raised when a requested database record is not found."""
    pass


class DatabaseOperationError(MemoryException):
    """Raised for general database execution/SQLAlchemy failures."""
    pass
