"""Assistant Runtime Foundation Subsystem for Auralis (Phase 13.1).

Highest-level orchestration layer uniting Brain Runtime (Phase 9), AI Runtime (Phase 10),
Operating System Runtime (Phase 11), and Execution Runtime (Phase 12).
"""

from brain.assistant.assistant_provider import AssistantProvider
from brain.assistant.assistant_runtime import AssistantRuntime
from brain.assistant.exceptions import (
    AssistantConfigurationError,
    AssistantException,
    AssistantInitializationError,
    AssistantRuntimeError,
    AssistantSessionError,
)
from brain.assistant.interfaces import (
    IAssistantHealthMonitor,
    IAssistantProvider,
    IAssistantRuntime,
    IAssistantSessionManager,
    IAssistantStatisticsCollector,
)
from brain.assistant.models import (
    AssistantCapabilities,
    AssistantConfiguration,
    AssistantContext,
    AssistantHealth,
    AssistantSession,
    AssistantState,
    AssistantStateEnum,
    AssistantStatistics,
    AssistantStatus,
)
from brain.assistant.runtime import (
    get_assistant_runtime,
    reset_assistant_runtime,
)

__all__ = [
    # Models
    "AssistantStateEnum",
    "AssistantState",
    "AssistantStatus",
    "AssistantCapabilities",
    "AssistantStatistics",
    "AssistantHealth",
    "AssistantContext",
    "AssistantSession",
    "AssistantConfiguration",
    # Exceptions
    "AssistantException",
    "AssistantInitializationError",
    "AssistantRuntimeError",
    "AssistantConfigurationError",
    "AssistantSessionError",
    # Interfaces
    "IAssistantProvider",
    "IAssistantRuntime",
    "IAssistantSessionManager",
    "IAssistantHealthMonitor",
    "IAssistantStatisticsCollector",
    # Implementation & Provider
    "AssistantProvider",
    "AssistantRuntime",
    # Singleton accessors
    "get_assistant_runtime",
    "reset_assistant_runtime",
]
