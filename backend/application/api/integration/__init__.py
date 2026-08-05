"""API Integration Gateway Runtime Package (Phase 15.9).

Provider-independent Integration Gateway Runtime establishing models, exceptions,
ABC interfaces, API gateway orchestrator, request coordinator, response coordinator,
integration provider, runtime coordinator, and singleton accessors.
"""

from backend.application.api.integration.api_gateway import ApiGateway
from backend.application.api.integration.exceptions import (
    ApiIntegrationException,
    PipelineExecutionException,
    RequestCoordinationException,
    ResponseCoordinationException,
)
from backend.application.api.integration.integration_provider import (
    IntegrationProvider,
)
from backend.application.api.integration.integration_runtime import (
    IntegrationRuntime,
)
from backend.application.api.integration.interfaces import (
    IApiGateway,
    IIntegrationProvider,
    IIntegrationRuntime,
    IRequestCoordinator,
    IResponseCoordinator,
)
from backend.application.api.integration.models import (
    ApiIntegrationRequest,
    ApiIntegrationResponse,
    ApiPipelineStage,
    ApiRequestContext,
    ApiResponseContext,
    IntegrationCapabilities,
    IntegrationDiagnostics,
    IntegrationHealth,
    IntegrationRuntimeState,
    IntegrationStatistics,
    PipelineStage,
)
from backend.application.api.integration.request_coordinator import (
    RequestCoordinator,
)
from backend.application.api.integration.response_coordinator import (
    ResponseCoordinator,
)
from backend.application.api.integration.runtime import (
    get_integration_provider,
    get_integration_runtime,
    reset_integration_provider,
    reset_integration_runtime,
    set_integration_provider,
    set_integration_runtime,
)

__all__ = [
    # Models & Enums
    "PipelineStage",
    "IntegrationRuntimeState",
    "ApiPipelineStage",
    "ApiIntegrationRequest",
    "ApiIntegrationResponse",
    "ApiRequestContext",
    "ApiResponseContext",
    "IntegrationCapabilities",
    "IntegrationStatistics",
    "IntegrationHealth",
    "IntegrationDiagnostics",
    # Exceptions
    "ApiIntegrationException",
    "RequestCoordinationException",
    "ResponseCoordinationException",
    "PipelineExecutionException",
    # Interfaces
    "IApiGateway",
    "IRequestCoordinator",
    "IResponseCoordinator",
    "IIntegrationProvider",
    "IIntegrationRuntime",
    # Implementations
    "ApiGateway",
    "RequestCoordinator",
    "ResponseCoordinator",
    "IntegrationProvider",
    "IntegrationRuntime",
    # Runtime Helpers
    "get_integration_runtime",
    "set_integration_runtime",
    "reset_integration_runtime",
    "get_integration_provider",
    "set_integration_provider",
    "reset_integration_provider",
]
