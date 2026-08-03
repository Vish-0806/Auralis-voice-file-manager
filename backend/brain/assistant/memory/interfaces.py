"""Abstract Interfaces for Assistant Memory & Context Integration (Phase 13.5).

Defines Python ABC abstract interfaces for context management, preference merging,
memory coordination, provider aggregation, and runtime orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.assistant.memory.models import (
    AssistantMemoryContext,
    AssistantMemoryHealth,
    AssistantMemorySnapshot,
    AssistantMemoryStatistics,
    AssistantPreference,
    AssistantWorkingContext,
)


class IAssistantContextManager(ABC):
    """Abstract interface for managing and merging context from multiple subsystem runtimes."""

    @abstractmethod
    def merge_contexts(
        self,
        contexts: List[AssistantMemoryContext],
        session_id: Optional[str] = None,
        token_budget: int = 4096,
    ) -> AssistantWorkingContext:
        """Merge, prioritize, deduplicate, and token-budget context units into an AssistantWorkingContext."""
        pass


class IAssistantPreferenceManager(ABC):
    """Abstract interface for user, assistant, and runtime preference management."""

    @abstractmethod
    def merge_preferences(
        self,
        user_prefs: Optional[Dict[str, Any]] = None,
        assistant_prefs: Optional[Dict[str, Any]] = None,
        runtime_prefs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Merge preferences deterministically with scope priority ordering."""
        pass

    @abstractmethod
    def register_preference(self, preference: AssistantPreference) -> None:
        """Register a preference setting."""
        pass


class IAssistantMemoryCoordinator(ABC):
    """Abstract interface for coordinating multi-runtime contexts into a unified AssistantMemorySnapshot."""

    @abstractmethod
    def create_snapshot(
        self,
        session_id: Optional[str] = None,
        conversation_runtime: Optional[Any] = None,
        dialogue_runtime: Optional[Any] = None,
        decision_runtime: Optional[Any] = None,
        execution_runtime: Optional[Any] = None,
        ai_memory_runtime: Optional[Any] = None,
        token_budget: int = 4096,
    ) -> AssistantMemorySnapshot:
        """Collect context from runtimes and produce a unified AssistantMemorySnapshot."""
        pass


class IAssistantMemoryProvider(ABC):
    """Abstract interface aggregating context manager, preference manager, and memory coordinator."""

    @property
    @abstractmethod
    def context_manager(self) -> IAssistantContextManager:
        """Get the assistant context manager."""
        pass

    @property
    @abstractmethod
    def preference_manager(self) -> IAssistantPreferenceManager:
        """Get the preference manager."""
        pass

    @property
    @abstractmethod
    def coordinator(self) -> IAssistantMemoryCoordinator:
        """Get the memory coordinator."""
        pass

    @abstractmethod
    def get_health(self) -> AssistantMemoryHealth:
        """Get diagnostic health snapshot."""
        pass

    @abstractmethod
    def get_statistics(self) -> AssistantMemoryStatistics:
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


class IAssistantMemoryRuntime(ABC):
    """Abstract interface for top-level Assistant Memory Integration Runtime orchestration."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize assistant memory runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown assistant memory runtime."""
        pass

    @abstractmethod
    def get_health(self) -> AssistantMemoryHealth:
        """Get overall health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> AssistantMemoryStatistics:
        """Get runtime performance statistics."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
