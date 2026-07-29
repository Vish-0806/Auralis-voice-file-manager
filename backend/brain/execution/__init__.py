"""Execution Engine subsystem package for Auralis."""

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
    DecisionType,
    ExecutionDecision,
)
from .execution_context import ExecutionContext
from .execution_coordinator import ExecutionCoordinator
from .execution_engine import ExecutionEngine, is_long_running_task
from .execution_history import ExecutionHistory
from .execution_models import ExecutionResult, ExecutionStatus, ExecutionStepResult
from .execution_monitor import (
    ExecutionMetrics,
    ExecutionMonitor,
    ExecutionStatistics,
    ExecutionSummary,
)
from .execution_policy import ExecutionPolicy
from .execution_scheduler import ExecutionScheduler
from .execution_session import ExecutionSession
from .execution_state import (
    ExecutionProgress,
    ExecutionSnapshot,
    ExecutionState,
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
from .runtime import (
    ExecutionRuntimeCoordinator,
    ExecutionRuntimeHealth,
    ExecutionRuntimeStatistics,
    ExecutionRuntimeStatus,
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
    "ExecutionStatus",
    "ExecutionStepResult",
    "ExecutionResult",
    "ExecutionPolicy",
    "ExecutionContext",
    "ExecutionSession",
    "ExecutionStepRunner",
    "ExecutionCoordinator",
    "ExecutionRuntimeStatus",
    "ExecutionRuntimeStatistics",
    "ExecutionRuntimeHealth",
    "ExecutionRuntimeCoordinator",
    "get_execution_runtime",
    "reset_execution_runtime",
    "ExecutionRecord",
    "ExecutionHistory",
    "ExecutionValidator",
    "ExecutionScheduler",
    "ExecutionEngine",
    "is_long_running_task",
    "ExecutionProgress",
    "ExecutionState",
    "ExecutionSnapshot",
    "ExecutionStateConfig",
    "ExecutionStateManager",
    "ExecutionMetrics",
    "ExecutionSummary",
    "ExecutionStatistics",
    "ExecutionMonitor",
    "DecisionType",
    "DecisionReason",
    "ExecutionDecision",
    "DecisionContext",
    "DecisionEngine",
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
