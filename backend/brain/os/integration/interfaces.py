"""Abstract interfaces for Integration Subsystem (Phase 11.9).

Defines canonical interfaces for Capability Registry, Request Router, Operation Dispatcher,
Execution Pipeline, Integration Provider, and Integration Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.os.integration.integration_models import (
    CapabilityDescriptor,
    ExecutionStatistics,
    IntegrationHealth,
    IntegrationStatus,
    OperationRequest,
    OperationResponse,
    OperationResult,
    OperationTarget,
)


class ICapabilityRegistry(ABC):
    """Interface for OS capability registration and discovery."""

    @abstractmethod
    def register(self, descriptor: CapabilityDescriptor) -> None:
        """Register a new OS capability."""
        pass

    @abstractmethod
    def unregister(self, capability_name: str) -> bool:
        """Unregister an existing capability."""
        pass

    @abstractmethod
    def lookup(self, capability_name: str) -> Optional[CapabilityDescriptor]:
        """Lookup capability descriptor by capability name."""
        pass

    @abstractmethod
    def get_capabilities(
        self, target: Optional[OperationTarget] = None
    ) -> List[CapabilityDescriptor]:
        """List all registered capabilities or filter by target category."""
        pass

    @abstractmethod
    def list_categories(self) -> List[OperationTarget]:
        """List all operation target categories with registered capabilities."""
        pass


class IRequestRouter(ABC):
    """Interface for resolving capabilities and validating operation requests."""

    @abstractmethod
    def route(self, request: OperationRequest) -> CapabilityDescriptor:
        """Resolve target capability for an operation request."""
        pass

    @abstractmethod
    def validate_request(self, request: OperationRequest) -> bool:
        """Validate request parameters and targets against registered capability schema."""
        pass


class IOperationDispatcher(ABC):
    """Interface for dispatching validated requests to target OS runtimes."""

    @abstractmethod
    def dispatch(
        self, request: OperationRequest, capability: CapabilityDescriptor
    ) -> OperationResult:
        """Dispatch operation request to underlying subsystem runtime."""
        pass


class IExecutionPipeline(ABC):
    """Interface for orchestrating the complete execution pipeline."""

    @abstractmethod
    def execute_pipeline(self, request: OperationRequest) -> OperationResponse:
        """Execute full request lifecycle pipeline."""
        pass


class IIntegrationProvider(ABC):
    """Interface for Integration Subsystem Provider."""

    @abstractmethod
    def get_capability_registry(self) -> ICapabilityRegistry:
        """Return capability registry."""
        pass

    @abstractmethod
    def get_request_router(self) -> IRequestRouter:
        """Return request router."""
        pass

    @abstractmethod
    def get_dispatcher(self) -> IOperationDispatcher:
        """Return operation dispatcher."""
        pass

    @abstractmethod
    def get_execution_pipeline(self) -> IExecutionPipeline:
        """Return execution pipeline."""
        pass

    @abstractmethod
    def execute(self, request: OperationRequest) -> OperationResponse:
        """Execute OS operation request through execution pipeline."""
        pass

    @abstractmethod
    def get_health(self) -> IntegrationHealth:
        """Return provider health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Return execution statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[CapabilityDescriptor]:
        """Return registered capability descriptors."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        pass


class IIntegrationRuntime(ABC):
    """Interface for Integration Runtime coordinator."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize integration runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown integration runtime."""
        pass

    @abstractmethod
    def register_provider(self, provider: IIntegrationProvider) -> None:
        """Register integration provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[IIntegrationProvider]:
        """Get registered integration provider."""
        pass

    @abstractmethod
    def execute(self, request: OperationRequest) -> OperationResponse:
        """Execute an operation request."""
        pass

    @abstractmethod
    def get_statistics(self) -> ExecutionStatistics:
        """Get integration runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> IntegrationStatus:
        """Get overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get runtime diagnostics dictionary."""
        pass
