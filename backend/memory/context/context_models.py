"""User Context Domain Models, Enum Types, and Custom Exceptions."""

from enum import Enum
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from memory.exceptions import MemoryException


# Custom exceptions for User Context Memory
class ContextError(MemoryException):
    """Base exception for all user context memory operations."""
    pass


class InvalidContextError(ContextError):
    """Raised when context validation fails (e.g. invalid type, incorrect schema)."""
    pass


class ExpiredContextError(ContextError):
    """Raised when attempting to access a context entry that has expired."""
    pass


class ContextType(str, Enum):
    """Enumeration of standard active context types supported by Auralis."""

    CURRENT_PROJECT = "current_project"
    ACTIVE_FOLDER = "active_folder"
    RECENT_FILES = "recent_files"
    RECENT_COMMANDS = "recent_commands"
    ACTIVE_WORKSPACE = "active_workspace"
    CURRENT_TERMINAL = "current_terminal"
    CURRENT_BROWSER = "current_browser"
    RECENT_CONVERSATION = "recent_conversation"
    CLIPBOARD = "clipboard"
    TEMPORARY = "temporary"


class ContextItem(BaseModel):
    """Container representing a single validated active context value with optional expiry.

    Attributes:
        value: The actual state/metadata value (e.g. list, string, dict).
        expires_at: Optional epoch timestamp (float) indicating when the entry expires.
        updated_at: Epoch timestamp (float) when the entry was last updated.
    """

    value: Any
    expires_at: Optional[float] = None
    updated_at: float = Field(default_factory=lambda: __import__("time").time())
