"""Abstract Interfaces for the Dialogue Management Subsystem (Phase 13.3).

Defines Python ABC abstract interfaces for session management, policy evaluation,
state tracking, provider aggregation, and runtime orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.assistant.dialogue.models import (
    DialogueContext,
    DialogueDecision,
    DialogueHealth,
    DialogueMode,
    DialoguePolicy,
    DialogueSession,
    DialogueState,
    DialogueStatistics,
    DialogueStatus,
    DialogueTurn,
)


class IDialogueManager(ABC):
    """Abstract interface for managing dialogue flow and session lifecycles."""

    @abstractmethod
    def create_session(
        self,
        conversation_id: Optional[str] = None,
        mode: DialogueMode = DialogueMode.DEFAULT,
        policy: Optional[DialoguePolicy] = None,
        context: Optional[DialogueContext] = None,
    ) -> DialogueSession:
        """Create and register a new dialogue session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[DialogueSession]:
        """Retrieve a dialogue session by ID."""
        pass

    @abstractmethod
    def create_turn(
        self,
        session_id: str,
        user_input: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DialogueTurn:
        """Create and register a new dialogue turn in a session."""
        pass

    @abstractmethod
    def update_status(
        self, session_id: str, new_status: DialogueStatus
    ) -> DialogueSession:
        """Update dialogue session status and validate state machine transitions."""
        pass

    @abstractmethod
    def complete_turn(
        self,
        session_id: str,
        turn_id: str,
        system_response: str,
        completed_status: DialogueStatus = DialogueStatus.IDLE,
    ) -> DialogueTurn:
        """Mark a dialogue turn complete with system response."""
        pass

    @abstractmethod
    def list_sessions(
        self, status: Optional[DialogueStatus] = None
    ) -> List[DialogueSession]:
        """List all active or filtered dialogue sessions."""
        pass


class IDialoguePolicyManager(ABC):
    """Abstract interface for evaluating dialogue policy decisions."""

    @abstractmethod
    def evaluate(
        self,
        session: DialogueSession,
        turn: DialogueTurn,
        policy: Optional[DialoguePolicy] = None,
    ) -> DialogueDecision:
        """Evaluate policy to determine next dialogue action, mode, clarification, and confirmation."""
        pass


class IDialogueStateManager(ABC):
    """Abstract interface for maintaining dialogue state snapshots and turn history."""

    @abstractmethod
    def get_state(self, session_id: str) -> Optional[DialogueState]:
        """Retrieve current dialogue state snapshot."""
        pass

    @abstractmethod
    def update_context(
        self, session_id: str, context_updates: Dict[str, Any]
    ) -> DialogueContext:
        """Merge context updates into session dialogue context."""
        pass

    @abstractmethod
    def get_turns(self, session_id: str) -> List[DialogueTurn]:
        """Retrieve turn history for a session."""
        pass


class IDialogueProvider(ABC):
    """Abstract interface aggregating dialogue managers, health, and statistics."""

    @property
    @abstractmethod
    def manager(self) -> IDialogueManager:
        """Get the dialogue manager."""
        pass

    @property
    @abstractmethod
    def policy_manager(self) -> IDialoguePolicyManager:
        """Get the policy manager."""
        pass

    @property
    @abstractmethod
    def state_manager(self) -> IDialogueStateManager:
        """Get the state manager."""
        pass

    @abstractmethod
    def get_health(self) -> DialogueHealth:
        """Get diagnostic health snapshot."""
        pass

    @abstractmethod
    def get_statistics(self) -> DialogueStatistics:
        """Get aggregated performance metrics."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize provider resources."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown provider resources."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        pass


class IDialogueRuntime(ABC):
    """Abstract interface for top-level Dialogue Runtime orchestration."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize dialogue runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown dialogue runtime."""
        pass

    @abstractmethod
    def get_health(self) -> DialogueHealth:
        """Get overall health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> DialogueStatistics:
        """Get runtime performance statistics."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
