"""Abstract Interfaces for the Assistant Runtime Subsystem (Phase 13.1).

Defines Python ABC abstract interfaces for provider integration, runtime orchestration,
session management, health monitoring, and statistics collection.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from brain.assistant.models import (
    AssistantCapabilities,
    AssistantHealth,
    AssistantSession,
    AssistantStatistics,
    AssistantStatus,
)


class IAssistantProvider(ABC):
    """Abstract interface aggregating assistant services, health, stats, capabilities, and lifecycle."""

    @abstractmethod
    def get_capabilities(self) -> AssistantCapabilities:
        """Return assistant capability specifications."""
        pass

    @abstractmethod
    def get_health(self) -> AssistantHealth:
        """Return aggregated real-time health metrics of assistant services."""
        pass

    @abstractmethod
    def get_statistics(self) -> AssistantStatistics:
        """Return assistant runtime diagnostic statistics."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize provider resources and underlying sub-runtimes."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shut down provider resources."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        pass


class IAssistantRuntime(ABC):
    """Abstract interface for the Assistant Runtime top-level orchestration layer."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the assistant runtime environment."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the assistant runtime environment."""
        pass

    @abstractmethod
    def get_status(self) -> AssistantStatus:
        """Return current status of the assistant runtime."""
        pass

    @abstractmethod
    def get_health(self) -> AssistantHealth:
        """Return overall health status of the assistant runtime."""
        pass

    @abstractmethod
    def get_statistics(self) -> AssistantStatistics:
        """Return execution and performance statistics."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Return whether runtime is initialized."""
        pass


class IAssistantSessionManager(ABC):
    """Abstract interface for managing assistant sessions and context variables."""

    @abstractmethod
    def create_session(self, context: Optional[Any] = None) -> AssistantSession:
        """Create and register a new assistant session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[AssistantSession]:
        """Retrieve an active assistant session by ID."""
        pass

    @abstractmethod
    def close_session(self, session_id: str) -> bool:
        """Close and terminate an active session."""
        pass

    @abstractmethod
    def list_sessions(self) -> Dict[str, AssistantSession]:
        """List all active sessions."""
        pass


class IAssistantHealthMonitor(ABC):
    """Abstract interface for assistant health checks."""

    @abstractmethod
    def check_health(self) -> AssistantHealth:
        """Perform a comprehensive diagnostic health check."""
        pass


class IAssistantStatisticsCollector(ABC):
    """Abstract interface for collecting assistant runtime performance metrics."""

    @abstractmethod
    def collect_statistics(self) -> AssistantStatistics:
        """Collect and return a snapshot of runtime statistics."""
        pass

    @abstractmethod
    def record_request(self, duration_ms: float = 0.0, success: bool = True) -> None:
        """Record an executed request metric."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset collected statistics."""
        pass
