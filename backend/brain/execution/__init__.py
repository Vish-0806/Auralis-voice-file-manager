"""Brain Execution Engine subsystem package for Auralis (Phase 12.1).

Exports canonical models, exceptions, interfaces, request analyzer, decision engine,
execution pipeline, execution provider, execution runtime, and legacy background task schedulers.
"""

from __future__ import annotations

from .background_job_scheduler import (
    BackgroundJob,
    BackgroundJobPersistenceHook,
    BackgroundJobPriority,
    BackgroundJobScheduler,
    BackgroundJobStatus,
    BackgroundJobTriggerType,
    BackgroundSchedulerConfig,
    NullBackgroundJobPersistenceHook,
    RecurringScheduleCalculator,
    RecurringTriggerValidator,
    TriggerValidationResult,
    convert_to_execution_request,
)
from .clarification_engine import (
    ClarificationChoice,
    ClarificationContext,
    ClarificationEngine,
    ClarificationRequest,
    ClarificationResponse,
    ClarificationType,
)
from .clarification_session import (
    ClarificationSession,
    ClarificationSessionConfig,
    ClarificationSessionManager,
    ClarificationSessionStatus,
)
from .decision_engine import (
    DecisionContext,
    DecisionEngine,
    DecisionReason,
)
from .exceptions import (
    ExecutionCancelled,
    ExecutionException,
    ExecutionFailure,
    ExecutionRoutingError,
    ExecutionValidationError,
)
from .execution_context import ExecutionContext
from .execution_coordinator import ExecutionCoordinator
from .execution_engine import ExecutionEngine, is_long_running_task
from .execution_history import ExecutionHistory
from .execution_models import (
    DecisionType,
    ExecutionContext as ExecutionContextModel,
    ExecutionDecision,
    ExecutionHealth,
    ExecutionMode,
    ExecutionRequest,
    ExecutionResult,
    ExecutionState,
    ExecutionStatistics,
    ExecutionStatus,
    ExecutionStepResult,
)
from .execution_monitor import (
    ExecutionMetrics,
    ExecutionMonitor,
    ExecutionSummary,
)
from .execution_pipeline import ExecutionPipeline
from .execution_policy import ExecutionPolicy
from .execution_provider import ExecutionProvider
from .execution_runtime import ExecutionRuntime, ExecutionRuntimeStatus
from .execution_scheduler import ExecutionScheduler
from .execution_session import ExecutionSession
from .execution_state import (
    ExecutionProgress,
    ExecutionSnapshot,
    ExecutionStateConfig,
)
from .execution_state_manager import ExecutionStateManager
from .execution_step_runner import ExecutionStepRunner
from .execution_validator import ExecutionValidator
from .failure_recovery import (
    FailureAnalysis,
    FailureCategory,
    FailureRecoveryEngine,
    RecoveryContext,
    RecoveryPlan,
    RecoveryStrategy,
)
from .interfaces import (
    IDecisionEngine,
    IExecutionCoordinator,
    IExecutionPipeline,
    IExecutionRuntime,
    IRequestAnalyzer,
)
from .long_running_task_manager import (
    LongRunningTask,
    LongRunningTaskConfig,
    LongRunningTaskManager,
    LongRunningTaskPriority,
    LongRunningTaskStatus,
    NullTaskPersistenceHook,
    TaskPersistenceHook,
)
from .models import ExecutionRecord
from .request_analyzer import RequestAnalyzer
from .runtime import (
    ExecutionRuntimeCoordinator,
    ExecutionRuntimeHealth,
    ExecutionRuntimeStatistics,
    get_execution_runtime,
    reset_execution_runtime,
)
from .task_events import (
    TaskEvent,
    TaskEventDispatcher,
    TaskEventListener,
    TaskEventType,
)

__all__ = [
    # Models & Enums
    "ExecutionRequest",
    "ExecutionContext",
    "ExecutionContextModel",
    "ExecutionDecision",
    "ExecutionResult",
    "ExecutionStatistics",
    "ExecutionHealth",
    "ExecutionStatus",
    "ExecutionStepResult",
    "ExecutionState",
    "DecisionType",
    "ExecutionMode",
    # Exceptions
    "ExecutionException",
    "ExecutionValidationError",
    "ExecutionRoutingError",
    "ExecutionFailure",
    "ExecutionCancelled",
    # Interfaces
    "IExecutionCoordinator",
    "IRequestAnalyzer",
    "IDecisionEngine",
    "IExecutionPipeline",
    "IExecutionRuntime",
    # Subsystem Core Components
    "RequestAnalyzer",
    "DecisionEngine",
    "DecisionReason",
    "DecisionContext",
    "ExecutionPipeline",
    "ExecutionProvider",
    "ExecutionRuntime",
    "ExecutionRuntimeStatus",
    "get_execution_runtime",
    "reset_execution_runtime",
    # Legacy Execution Engine Components
    "ExecutionPolicy",
    "ExecutionSession",
    "ExecutionStepRunner",
    "ExecutionCoordinator",
    "ExecutionRuntimeCoordinator",
    "ExecutionRuntimeStatistics",
    "ExecutionRuntimeHealth",
    "ExecutionRecord",
    "ExecutionHistory",
    "ExecutionValidator",
    "ExecutionScheduler",
    "ExecutionEngine",
    "is_long_running_task",
    "ExecutionProgress",
    "ExecutionSnapshot",
    "ExecutionStateConfig",
    "ExecutionStateManager",
    "ExecutionMetrics",
    "ExecutionSummary",
    "ExecutionMonitor",
    "FailureCategory",
    "RecoveryStrategy",
    "FailureAnalysis",
    "RecoveryPlan",
    "RecoveryContext",
    "FailureRecoveryEngine",
    "ClarificationType",
    "ClarificationChoice",
    "ClarificationRequest",
    "ClarificationResponse",
    "ClarificationContext",
    "ClarificationEngine",
    "ClarificationSessionStatus",
    "ClarificationSession",
    "ClarificationSessionConfig",
    "ClarificationSessionManager",
    "LongRunningTaskStatus",
    "LongRunningTaskPriority",
    "LongRunningTask",
    "LongRunningTaskConfig",
    "LongRunningTaskManager",
    "TaskPersistenceHook",
    "NullTaskPersistenceHook",
    "TaskEventType",
    "TaskEvent",
    "TaskEventListener",
    "TaskEventDispatcher",
    "BackgroundJobStatus",
    "BackgroundJobPriority",
    "BackgroundJobTriggerType",
    "BackgroundJob",
    "BackgroundSchedulerConfig",
    "BackgroundJobScheduler",
    "convert_to_execution_request",
    "TriggerValidationResult",
    "RecurringTriggerValidator",
    "RecurringScheduleCalculator",
    "BackgroundJobPersistenceHook",
    "NullBackgroundJobPersistenceHook",
]
