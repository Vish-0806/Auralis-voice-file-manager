"""Integration Subsystem for Auralis Operating System Abstraction (Phase 11.9).

Exports domain models, enums, exceptions, abstract interfaces, services,
provider, runtime coordinator, and singleton accessors.
"""

from brain.os.integration.capability_registry import CapabilityRegistry
from brain.os.integration.exceptions import (
    CapabilityNotFoundError,
    ExecutionPipelineError,
    IntegrationException,
    OperationDispatchError,
    OperationValidationError,
)
from brain.os.integration.execution_pipeline import ExecutionPipeline
from brain.os.integration.integration_models import (
    CapabilityDescriptor,
    DispatchStrategy,
    ExecutionState,
    ExecutionStatistics,
    ExecutionSummary,
    IntegrationHealth,
    IntegrationStatus,
    OperationContext,
    OperationRequest,
    OperationResponse,
    OperationResult,
    OperationTarget,
    OperationType,
)
from brain.os.integration.integration_provider import IntegrationProvider
from brain.os.integration.integration_runtime import IntegrationRuntime
from brain.os.integration.interfaces import (
    ICapabilityRegistry,
    IExecutionPipeline,
    IIntegrationProvider,
    IIntegrationRuntime,
    IOperationDispatcher,
    IRequestRouter,
)
from brain.os.integration.operation_dispatcher import OperationDispatcher
from brain.os.integration.request_router import RequestRouter
from brain.os.integration.runtime import (
    get_integration_runtime,
    reset_integration_runtime,
)

__all__ = [
    # Enums
    "OperationTarget",
    "OperationType",
    "ExecutionState",
    "DispatchStrategy",
    # Models
    "OperationContext",
    "OperationRequest",
    "OperationResult",
    "ExecutionSummary",
    "OperationResponse",
    "CapabilityDescriptor",
    "ExecutionStatistics",
    "IntegrationHealth",
    "IntegrationStatus",
    # Exceptions
    "IntegrationException",
    "CapabilityNotFoundError",
    "OperationDispatchError",
    "ExecutionPipelineError",
    "OperationValidationError",
    # Interfaces
    "ICapabilityRegistry",
    "IRequestRouter",
    "IOperationDispatcher",
    "IExecutionPipeline",
    "IIntegrationProvider",
    "IIntegrationRuntime",
    # Services & Implementations
    "CapabilityRegistry",
    "RequestRouter",
    "OperationDispatcher",
    "ExecutionPipeline",
    "IntegrationProvider",
    "IntegrationRuntime",
    # Singleton Accessors
    "get_integration_runtime",
    "reset_integration_runtime",
]
