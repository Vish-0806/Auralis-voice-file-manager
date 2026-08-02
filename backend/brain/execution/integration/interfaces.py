"""Abstract Base Class interfaces for the Auralis Execution Runtime Integration (Phase 12.9).

Defines canonical interfaces for capability registry, execution router, execution pipeline, provider, and runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.execution.integration.integration_models import (
    ExecutionCapability,
    ExecutionTarget,
    IntegrationHealth,
    IntegrationRequest,
    IntegrationResponse,
    IntegrationStatistics,
    PipelineStageRecord,
)


class ICapabilityRegistry(ABC):
    """Interface for managing registered execution capabilities."""

    @abstractmethod
    def register_capability(
        self,
        name: str,
        target: ExecutionTarget,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCapability:
        """Register a new execution capability."""
        pass

    @abstractmethod
    def get_capability(self, capability_id: str) -> Optional[ExecutionCapability]:
        """Fetch capability by capability_id."""
        pass

    @abstractmethod
    def list_capabilities(self, target: Optional[ExecutionTarget] = None) -> List[ExecutionCapability]:
        """List all capabilities matching optional target filter."""
        pass


class IExecutionRouter(ABC):
    """Interface for routing execution requests to subsystem targets."""

    @abstractmethod
    def route_request(self, request: IntegrationRequest) -> ExecutionTarget:
        """Determine appropriate ExecutionTarget for a request."""
        pass


class IExecutionPipeline(ABC):
    """Interface for orchestrating multi-stage pipeline execution."""

    @abstractmethod
    def execute_pipeline(self, request: IntegrationRequest, target: ExecutionTarget) -> IntegrationResponse:
        """Orchestrate multi-stage pipeline execution."""
        pass


class IIntegrationProvider(ABC):
    """Interface for aggregate Integration Provider."""

    @abstractmethod
    def process_request(self, request: IntegrationRequest) -> IntegrationResponse:
        """Process an integration request through the execution pipeline."""
        pass

    @abstractmethod
    def health_check(self) -> IntegrationHealth:
        """Report component health statuses across all execution subsystems."""
        pass

    @abstractmethod
    def get_statistics(self) -> IntegrationStatistics:
        """Return snapshot of aggregate integration statistics."""
        pass


class IIntegrationRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize integration runtime lifecycle."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down integration runtime lifecycle."""
        pass

    @abstractmethod
    def health_check(self) -> IntegrationHealth:
        """Fetch real-time health diagnostic status."""
        pass

    @abstractmethod
    def get_statistics(self) -> IntegrationStatistics:
        """Fetch snapshot of integration statistics."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset integration statistics and transient state."""
        pass
