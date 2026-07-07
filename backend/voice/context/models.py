"""Defines the data models used by the context awareness subsystem."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ContextState:
    """Stores temporary session variables for reference resolution.

    Attributes:
        current_file: The name or path of the last referenced file.
        current_folder: The name or path of the last referenced folder.
        current_search_results: List of file/folder names from the last search operation.
        current_capability: The name of the last executed capability module.
        last_intent: The classification of the last processed user intent.
        last_execution_result: Plain text output from the last execution result.
        pending_confirmation: Dict representing action parameters awaiting confirm/cancel.
    """

    current_file: Optional[str] = None
    current_folder: Optional[str] = None
    current_search_results: List[str] = field(default_factory=list)
    current_capability: Optional[str] = None
    last_intent: Optional[str] = None
    last_execution_result: Optional[str] = None
    pending_confirmation: Optional[Dict[str, Any]] = None


@dataclass
class ResolutionResult:
    """The outcome of a reference resolution attempt.

    Attributes:
        resolved_command: The plain text command after reference substitution.
        requires_clarification: True if a reference was ambiguous or unresolvable.
        clarification_prompt: Clarification question to speak back to the user.
    """

    resolved_command: str
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None
