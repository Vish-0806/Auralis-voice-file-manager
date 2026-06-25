"""
Module: backend.core.exceptions

Responsibility:
    Defines the structured exception hierarchy for Auralis Core orchestration.
    Standardizes error propagation, logging categories, and recovery procedures.

This module SHOULD:
    - Define a base exception class (AuralisCoreException) inheriting from built-in Exception.
    - Declare distinct exceptions for distinct phases (Sessions, Planning, Dispatches, Safety).
    - Support details dictionaries for passing metadata (e.g., failed action names or session ids).

This module should NEVER:
    - Import external frameworks or application modules.
    - Raise raw generic exceptions without context.
    - Include recovery logic, handlers, or logs reporting.
"""

from typing import Any, Dict, Optional


class AuralisCoreException(Exception):
    """Base exception class for all Auralis Core errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SessionException(AuralisCoreException):
    """Raised when session creation, loading, or synchronization fails."""
    pass


class PlannerException(AuralisCoreException):
    """Raised when the AI Brain or Planner fails to construct a valid plan."""
    pass


class DispatcherException(AuralisCoreException):
    """Raised when executing capability actions fails or times out."""
    pass


class ContextException(AuralisCoreException):
    """Raised when environment contexts or active profiles cannot be resolved."""
    pass


class SecurityException(AuralisCoreException):
    """Raised when policy limits are violated or user confirmations are denied."""
    pass
