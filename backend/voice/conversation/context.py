"""Defines context storage for active conversation sessions."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ConversationContext:
    """Stores session variables to maintain state across multiple commands.

    Attributes:
        current_file: Name or path of the file last referenced.
        current_folder: Name or path of the directory last referenced.
        last_command: The plain text of the last successfully processed command.
        last_response: The response message generated for the last command.
        pending_confirmation: Dict representing action parameters awaiting confirm/cancel.
        metadata: Key-value metadata store for future extensibility.
    """

    current_file: Optional[str] = None
    current_folder: Optional[str] = None
    last_command: Optional[str] = None
    last_response: Optional[str] = None
    pending_confirmation: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def clear(self) -> None:
        """Resets the context fields back to default state."""
        self.current_file = None
        self.current_folder = None
        self.last_command = None
        self.last_response = None
        self.pending_confirmation = None
        self.metadata.clear()
