"""Command Execution Orchestrator subsystem package for Auralis (Phase 12.3).

Exports domain models, enums, exceptions, interfaces, coordinator, router, tracker,
orchestrator, provider, runtime lifecycle manager, and global singleton accessors.
"""

from .exceptions import (
    ExecutionAbortError,
    ExecutionCoordinationError,
    ExecutionOrchestratorException,
    ExecutionPreparationError,
    ExecutionRoutingError,
)
from .execution_coordinator import ExecutionCoordinator
from .execution_orchestrator import ExecutionOrchestrator
from .execution_provider import ExecutionProvider
from .execution_router import ExecutionRouter
from .execution_runtime import ExecutionRuntime, OrchestratorRuntimeStatus
from .execution_tracker import ExecutionTracker
from .interfaces import (
    IExecutionCoordinator,
    IExecutionOrchestrator,
    IExecutionProvider,
    IExecutionRouter,
    IExecutionRuntime,
    IExecutionTracker,
)
from .orchestrator_models import (
    ExecutionContext,
    ExecutionHealth,
    ExecutionMode,
    ExecutionPlanReference,
    ExecutionPriority,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStage,
    ExecutionStageType,
    ExecutionState,
    ExecutionStatistics,
    ExecutionSummary,
    OrchestrationStatus,
)
from .runtime import get_orchestrator_runtime, reset_orchestrator_runtime

__all__ = [
    # Models & Enums
    "ExecutionStageType",
    "ExecutionState",
    "ExecutionMode",
    "ExecutionPriority",
    "OrchestrationStatus",
    "ExecutionRequest",
    "ExecutionContext",
    "ExecutionPlanReference",
    "ExecutionStage",
    "ExecutionResult",
    "ExecutionSummary",
    "ExecutionStatistics",
    "ExecutionHealth",
    # Exceptions
    "ExecutionOrchestratorException",
    "ExecutionPreparationError",
    "ExecutionRoutingError",
    "ExecutionCoordinationError",
    "ExecutionAbortError",
    # Interfaces
    "IExecutionCoordinator",
    "IExecutionRouter",
    "IExecutionTracker",
    "IExecutionOrchestrator",
    "IExecutionProvider",
    "IExecutionRuntime",
    # Subsystem Core Components
    "ExecutionCoordinator",
    "ExecutionRouter",
    "ExecutionTracker",
    "ExecutionOrchestrator",
    "ExecutionProvider",
    "ExecutionRuntime",
    "OrchestratorRuntimeStatus",
    # Global Accessors
    "get_orchestrator_runtime",
    "reset_orchestrator_runtime",
]
