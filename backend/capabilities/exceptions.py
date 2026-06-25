"""
Module: backend.capabilities.exceptions

Responsibility:
    Defines the custom exceptions tree for the capabilities modules.

Future Expansion:
    Support error-code mapping for IPC integrations.
"""

from backend.core.exceptions import AuralisCoreException


class CapabilityException(AuralisCoreException):
    """Base exception class for capability operations."""
    pass


class CapabilityNotFoundException(CapabilityException):
    """Raised when a requested capability is not registered."""
    pass


class ActionExecutionException(CapabilityException):
    """Raised when a specific capability tool action fails during execution."""
    pass
