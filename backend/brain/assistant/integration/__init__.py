"""Assistant Runtime Integration Layer for Auralis (Phase 13.9).

Top-level integration gateway for the entire Assistant architecture. Coordinates all Phase 13 Assistant
runtimes and Phase 9-12 system runtimes without duplicating AI, memory, voice, or execution engines.
"""

from brain.assistant.integration.assistant_coordinator import AssistantCoordinator
from brain.assistant.integration.assistant_integration_provider import AssistantIntegrationProvider
from brain.assistant.integration.assistant_integration_runtime import AssistantIntegrationRuntime
from brain.assistant.integration.exceptions import (
    AssistantIntegrationException,
    AssistantPipelineException,
    AssistantRoutingException,
    AssistantSynchronizationException,
    AssistantValidationException,
)
from brain.assistant.integration.health_aggregator import HealthAggregator
from brain.assistant.integration.interfaces import (
    IAssistantCoordinator,
    IAssistantIntegrationProvider,
    IAssistantIntegrationRuntime,
    IHealthAggregator,
    IPipelineCoordinator,
    IRuntimeRegistry,
)
from brain.assistant.integration.models import (
    AssistantExecutionSummary,
    AssistantIntegrationCapabilities,
    AssistantIntegrationContext,
    AssistantIntegrationHealth,
    AssistantIntegrationRequest,
    AssistantIntegrationResponse,
    AssistantIntegrationSession,
    AssistantIntegrationState,
    AssistantIntegrationStatistics,
    AssistantMode,
    AssistantRuntimeSnapshot,
    IntegrationStage,
    IntegrationState,
    IntegrationStatus,
    PipelineState,
)
from brain.assistant.integration.pipeline_coordinator import PipelineCoordinator
from brain.assistant.integration.runtime import (
    get_assistant_integration_runtime,
    reset_assistant_integration_runtime,
)
from brain.assistant.integration.runtime_registry import RuntimeRegistry

__all__ = [
    # Enums & Models
    "IntegrationState",
    "IntegrationStage",
    "IntegrationStatus",
    "PipelineState",
    "AssistantMode",
    "AssistantExecutionSummary",
    "AssistantRuntimeSnapshot",
    "AssistantIntegrationContext",
    "AssistantIntegrationRequest",
    "AssistantIntegrationResponse",
    "AssistantIntegrationState",
    "AssistantIntegrationSession",
    "AssistantIntegrationCapabilities",
    "AssistantIntegrationStatistics",
    "AssistantIntegrationHealth",
    # Exceptions
    "AssistantIntegrationException",
    "AssistantPipelineException",
    "AssistantRoutingException",
    "AssistantSynchronizationException",
    "AssistantValidationException",
    # Interfaces
    "IRuntimeRegistry",
    "IPipelineCoordinator",
    "IAssistantCoordinator",
    "IHealthAggregator",
    "IAssistantIntegrationProvider",
    "IAssistantIntegrationRuntime",
    # Components & Registries
    "RuntimeRegistry",
    "PipelineCoordinator",
    "AssistantCoordinator",
    "HealthAggregator",
    "AssistantIntegrationProvider",
    "AssistantIntegrationRuntime",
    # Singleton accessors
    "get_assistant_integration_runtime",
    "reset_assistant_integration_runtime",
]
