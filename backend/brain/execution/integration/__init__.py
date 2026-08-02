"""Execution Runtime Integration package for Auralis (Phase 12.9).

Exports domain models, enums, exceptions, interfaces, capability registry, execution router,
execution pipeline, provider, runtime lifecycle manager, and global singleton accessors.
"""

from .capability_registry import CapabilityRegistry
from .exceptions import (
    CapabilityError,
    IntegrationException,
    IntegrationRuntimeError,
    PipelineExecutionError,
    RoutingError,
)
from .execution_pipeline import ExecutionPipeline
from .execution_provider import ExecutionProvider
from .execution_router import ExecutionRouter
from .execution_runtime import ExecutionRuntime, ExecutionRuntimeStatus
from .integration_models import (
    ExecutionCapability,
    ExecutionPriority,
    ExecutionStage,
    ExecutionStatus,
    ExecutionTarget,
    IntegrationHealth,
    IntegrationRequest,
    IntegrationResponse,
    IntegrationStatistics,
    PipelineStageRecord,
)

from .interfaces import (
    ICapabilityRegistry,
    IExecutionPipeline,
    IExecutionRouter,
    IIntegrationProvider,
    IIntegrationRuntime,
)
from .runtime import get_execution_runtime, reset_execution_runtime

__all__ = [
    # Enums & Models
    "ExecutionStage",
    "ExecutionStatus",
    "ExecutionTarget",
    "ExecutionPriority",
    "ExecutionCapability",
    "IntegrationRequest",
    "IntegrationResponse",
    "PipelineStageRecord",
    "IntegrationStatistics",
    "IntegrationHealth",
    # Exceptions
    "IntegrationException",
    "CapabilityError",
    "RoutingError",
    "PipelineExecutionError",
    "IntegrationRuntimeError",
    # Interfaces
    "ICapabilityRegistry",
    "IExecutionRouter",
    "IExecutionPipeline",
    "IIntegrationProvider",
    "IIntegrationRuntime",
    # Core Components
    "CapabilityRegistry",
    "ExecutionRouter",
    "ExecutionPipeline",
    "ExecutionProvider",
    "ExecutionRuntime",
    "ExecutionRuntimeStatus",
    # Global Accessors
    "get_execution_runtime",
    "reset_execution_runtime",
]
