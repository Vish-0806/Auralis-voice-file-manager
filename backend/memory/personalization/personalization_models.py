"""User Personalization exceptions and domain models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from memory.exceptions import MemoryException


# Custom Exceptions
class PersonalizationError(MemoryException):
    """Base exception for all personalization subsystem errors."""
    pass


class InvalidPersonalizationConfigError(PersonalizationError):
    """Raised when personalization validator detects invalid schemas or parameters."""
    pass


class UserProfile(BaseModel):
    """Aggregated personalization profile of a user.

    Attributes:
        user_id: Target user identifier.
        active_workspace_path: Current directory path from context or workspace.
        preferences: Consolidated dictionary of key preferences.
        active_routines_count: Count of accepted learned routines.
        recent_actions: Short list of recently run execution actions.
    """

    user_id: int
    active_workspace_path: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    active_routines_count: int = 0
    recent_actions: List[str] = Field(default_factory=list)


class PersonalizedContext(BaseModel):
    """Unified execution state parameters resolved via priority rules.

    Attributes:
        user_id: Target user identifier.
        session_id: Active session identifier.
        resolved_settings: The resolved settings values (e.g. theme, editor).
        source_mapping: Mapping of each resolved setting key to its priority source name.
    """

    user_id: int
    session_id: str
    resolved_settings: Dict[str, Any] = Field(default_factory=dict)
    source_mapping: Dict[str, str] = Field(default_factory=dict)


class PersonalizationSuggestion(BaseModel):
    """Personalized suggestions generated based on context analysis.

    Attributes:
        type: The suggestion category ('workspace_restore', 'routine_trigger').
        message: Readable summary recommending the change.
        payload: Metadata configuration data necessary to execute recommended suggestion.
    """

    type: str
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)
