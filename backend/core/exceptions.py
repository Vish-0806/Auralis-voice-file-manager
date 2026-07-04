"""Core exception contracts for Auralis.

The exception hierarchy is intentionally small and reusable. It supports the
new contract layer while preserving the legacy base exception name used by the
current codebase.
"""

from __future__ import annotations

from typing import Any


class AuralisException(Exception):
    """Base exception for all Auralis core errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuralisCoreException(AuralisException):
    """Compatibility alias for the legacy core exception base class."""


class PlanningException(AuralisCoreException):
    """Raised when planning fails or produces an invalid plan."""


class DispatchException(AuralisCoreException):
    """Raised when dispatching a plan fails."""


class CapabilityException(AuralisCoreException):
    """Raised when a capability contract is violated or execution fails."""


class ValidationException(AuralisCoreException):
    """Raised when input or contract validation fails."""


class SessionException(AuralisCoreException):
    """Raised when session creation, loading, or synchronization fails."""


class PlannerException(PlanningException):
    """Legacy alias for planning failures."""


class DispatcherException(DispatchException):
    """Legacy alias for dispatch failures."""


class ContextException(AuralisCoreException):
    """Raised when session or environment context cannot be resolved."""


class SecurityException(AuralisCoreException):
    """Raised when a policy or permission boundary is violated."""


__all__ = [
    "AuralisException",
    "AuralisCoreException",
    "PlanningException",
    "DispatchException",
    "CapabilityException",
    "ValidationException",
    "SessionException",
    "PlannerException",
    "DispatcherException",
    "ContextException",
    "SecurityException",
]
