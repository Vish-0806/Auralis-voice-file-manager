"""Automation & Scheduling Runtime package for Auralis (Phase 12.6).

Exports domain models, enums, exceptions, interfaces, scheduler, trigger engine, executor,
history store, provider, runtime lifecycle manager, and global singleton accessors.
"""

from .automation_executor import AutomationExecutor
from .automation_history_store import AutomationHistoryStore
from .automation_models import (
    AutomationContext,
    AutomationExecution,
    AutomationExecutionMode,
    AutomationHealth,
    AutomationHistory,
    AutomationPriority,
    AutomationRule,
    AutomationSchedule,
    AutomationScheduleType,
    AutomationStatistics,
    AutomationStatus,
    AutomationTrigger,
    AutomationTriggerType,
)
from .automation_provider import AutomationProvider
from .automation_runtime import AutomationRuntime, AutomationRuntimeStatus
from .automation_scheduler import AutomationScheduler
from .automation_trigger_engine import AutomationTriggerEngine

from .exceptions import (
    AutomationException,
    AutomationExecutionError,
    AutomationPersistenceError,
    AutomationScheduleError,
    AutomationTriggerError,
)

from .interfaces import (
    IAutomationExecutor,
    IAutomationHistory,
    IAutomationProvider,
    IAutomationRuntime,
    IAutomationScheduler,
    IAutomationTriggerEngine,
)
from .runtime import get_automation_runtime, reset_automation_runtime

__all__ = [
    # Enums & Models
    "AutomationStatus",
    "AutomationTriggerType",
    "AutomationScheduleType",
    "AutomationPriority",
    "AutomationExecutionMode",
    "AutomationSchedule",
    "AutomationTrigger",
    "AutomationRule",
    "AutomationContext",
    "AutomationExecution",
    "AutomationHistory",
    "AutomationStatistics",
    "AutomationHealth",
    # Exceptions
    "AutomationException",
    "AutomationTriggerError",
    "AutomationScheduleError",
    "AutomationExecutionError",
    "AutomationPersistenceError",
    # Interfaces
    "IAutomationScheduler",
    "IAutomationTriggerEngine",
    "IAutomationExecutor",
    "IAutomationHistory",
    "IAutomationProvider",
    "IAutomationRuntime",
    # Core Components
    "AutomationScheduler",
    "AutomationTriggerEngine",
    "AutomationExecutor",
    "AutomationHistoryStore",
    "AutomationProvider",
    "AutomationRuntime",
    "AutomationRuntimeStatus",
    # Global Accessors
    "get_automation_runtime",
    "reset_automation_runtime",
]
