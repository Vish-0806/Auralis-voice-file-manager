"""
Module: backend.os.exceptions

Responsibility:
    Defines exception schemas for OSAL adapters and operations.

Future Expansion:
    Support OS error-code translation maps.
"""

from core.exceptions import AuralisCoreException


class OSALException(AuralisCoreException):
    """Base exception class for all OS abstraction layer errors."""
    pass


class PlatformMismatchException(OSALException):
    """Raised when an adapter is loaded on an incompatible operating system."""
    pass


class OSActionFailedException(OSALException):
    """Raised when an underlying OS-level operation fails."""
    pass
