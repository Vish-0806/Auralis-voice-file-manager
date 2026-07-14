"""User Routine Learning exceptions and models."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from memory.exceptions import MemoryException


# Custom Exceptions
class LearningError(MemoryException):
    """Base exception for all routine learning operations."""
    pass


class InvalidRoutineError(LearningError):
    """Raised when routine structure validation fails."""
    pass


class RoutineNotFoundError(LearningError):
    """Raised when the specified learned routine is not found."""
    pass


class RoutineSuggestion(BaseModel):
    """Data container for suggested user routines discovered by history mining.

    Attributes:
        trigger_event: Event string or action that triggers the sequence.
        action_sequence: List of action configurations to execute in order.
        confidence_score: Derived strength score (0.0 to 1.0) of pattern.
        status: The suggestion approval status ('pending', 'accepted', 'rejected').
    """

    trigger_event: str
    action_sequence: Dict[str, Any]
    confidence_score: float = 0.0
    status: str = "pending"
