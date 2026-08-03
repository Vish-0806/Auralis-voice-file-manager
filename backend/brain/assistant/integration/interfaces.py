"""Abstract Interfaces for Assistant Runtime Integration Layer (Phase 13.9).

Defines Python ABC abstract interfaces for runtime registration, pipeline coordination,
assistant coordination, health aggregation, provider aggregation, and top-level integration runtime orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.assistant.integration.models import (
    AssistantExecutionSummary,
    AssistantIntegrationCapabilities,
    AssistantIntegrationContext,
    AssistantIntegrationHealth,
    AssistantIntegrationRequest,
    AssistantIntegrationResponse,
    AssistantIntegrationStatistics,
    AssistantRuntimeSnapshot,
    IntegrationStage,
)


class IRuntimeRegistry(ABC):
    """Abstract interface for registering, looking up, and inspecting sub-runtimes."""

    @abstractmethod
    def register_runtime(
        self,
        name: str,
        runtime_instance: Any,
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
    ) -> None:
        """Register a sub-runtime instance."""
        pass

    @abstractmethod
    def get_runtime(self, name: str) -> Optional[Any]:
        """Lookup a registered sub-runtime by name."""
        pass

    @abstractmethod
    def list_snapshots(self) -> List[AssistantRuntimeSnapshot]:
        """List snapshots of all registered runtimes."""
        pass

    @abstractmethod
    def is_available(self, name: str) -> bool:
        """Check if a runtime is registered and available."""
        pass


class IPipelineCoordinator(ABC):
    """Abstract interface for coordinating the complete assistant pipeline sequence."""

    @abstractmethod
    def execute_pipeline(
        self,
        request: AssistantIntegrationRequest,
        registry: IRuntimeRegistry,
    ) -> List[AssistantExecutionSummary]:
        """Execute the assistant pipeline across Conversation -> Dialogue -> Decision -> Memory -> Execution -> Response -> Voice -> Proactive stages."""
        pass


class IAssistantCoordinator(ABC):
    """Abstract interface for coordinating all assistant sub-runtimes into a unified response."""

    @abstractmethod
    def handle_request(
        self,
        request: AssistantIntegrationRequest,
        registry: IRuntimeRegistry,
        pipeline_coordinator: IPipelineCoordinator,
    ) -> AssistantIntegrationResponse:
        """Handle integration request and synthesize unified AssistantIntegrationResponse."""
        pass


class IHealthAggregator(ABC):
    """Abstract interface for aggregating health metrics across all 12 assistant and system runtimes."""

    @abstractmethod
    def aggregate_health(self, registry: IRuntimeRegistry) -> AssistantIntegrationHealth:
        """Collect diagnostic health snapshots across all registered runtimes and calculate availability percentage."""
        pass


class IAssistantIntegrationProvider(ABC):
    """Abstract interface aggregating runtime registry, pipeline coordinator, assistant coordinator, and health aggregator."""

    @property
    @abstractmethod
    def registry(self) -> IRuntimeRegistry:
        """Get the runtime registry."""
        pass

    @property
    @abstractmethod
    def pipeline_coordinator(self) -> IPipelineCoordinator:
        """Get the pipeline coordinator."""
        pass

    @property
    @abstractmethod
    def assistant_coordinator(self) -> IAssistantCoordinator:
        """Get the assistant coordinator."""
        pass

    @property
    @abstractmethod
    def health_aggregator(self) -> IHealthAggregator:
        """Get the health aggregator."""
        pass

    @abstractmethod
    def get_capabilities(self) -> AssistantIntegrationCapabilities:
        """Get aggregated integration capabilities."""
        pass

    @abstractmethod
    def get_health(self) -> AssistantIntegrationHealth:
        """Get unified health report."""
        pass

    @abstractmethod
    def get_statistics(self) -> AssistantIntegrationStatistics:
        """Get aggregated integration statistics."""
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


class IAssistantIntegrationRuntime(ABC):
    """Abstract interface for top-level Assistant Runtime Integration Layer orchestration."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize integration runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown integration runtime."""
        pass

    @abstractmethod
    def restart(self) -> None:
        """Restart integration runtime."""
        pass

    @abstractmethod
    def get_health(self) -> AssistantIntegrationHealth:
        """Get overall health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> AssistantIntegrationStatistics:
        """Get runtime performance statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> AssistantIntegrationCapabilities:
        """Get integration capabilities."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
