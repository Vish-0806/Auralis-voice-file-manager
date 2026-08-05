"""API Middleware Runtime Package (Phase 15.3).

Provider-independent Middleware Runtime establishing middleware models, exceptions,
ABC interfaces, registry, pipeline manager, executor, middleware provider,
middleware runtime coordinator, and singleton accessors.
"""

from backend.application.api.middleware.exceptions import (
    DuplicateMiddlewareException,
    MiddlewareException,
    MiddlewareExecutionException,
    MiddlewareRegistrationException,
    PipelineException,
)
from backend.application.api.middleware.interfaces import (
    IMiddlewareExecutor,
    IMiddlewareProvider,
    IMiddlewareRegistry,
    IMiddlewareRuntime,
    IPipelineManager,
)
from backend.application.api.middleware.middleware_executor import (
    MiddlewareExecutor,
)
from backend.application.api.middleware.middleware_provider import (
    MiddlewareProvider,
)
from backend.application.api.middleware.middleware_registry import (
    MiddlewareRegistry,
)
from backend.application.api.middleware.middleware_runtime import (
    MiddlewareRuntime,
)
from backend.application.api.middleware.models import (
    ApiMiddleware,
    MiddlewareCapabilities,
    MiddlewareContext,
    MiddlewareDiagnostics,
    MiddlewareExecution,
    MiddlewareHealth,
    MiddlewareResult,
    MiddlewareRuntimeState,
    MiddlewareStage,
    MiddlewareState,
    MiddlewareStatistics,
)
from backend.application.api.middleware.pipeline_manager import PipelineManager
from backend.application.api.middleware.runtime import (
    get_middleware_provider,
    get_middleware_runtime,
    reset_middleware_provider,
    reset_middleware_runtime,
    set_middleware_provider,
    set_middleware_runtime,
)

__all__ = [
    # Models & Enums
    "MiddlewareStage",
    "MiddlewareState",
    "MiddlewareRuntimeState",
    "ApiMiddleware",
    "MiddlewareContext",
    "MiddlewareExecution",
    "MiddlewareResult",
    "MiddlewareCapabilities",
    "MiddlewareStatistics",
    "MiddlewareHealth",
    "MiddlewareDiagnostics",
    # Exceptions
    "MiddlewareException",
    "MiddlewareRegistrationException",
    "MiddlewareExecutionException",
    "PipelineException",
    "DuplicateMiddlewareException",
    # Interfaces
    "IMiddlewareRegistry",
    "IPipelineManager",
    "IMiddlewareExecutor",
    "IMiddlewareProvider",
    "IMiddlewareRuntime",
    # Implementations
    "MiddlewareRegistry",
    "PipelineManager",
    "MiddlewareExecutor",
    "MiddlewareProvider",
    "MiddlewareRuntime",
    # Runtime Helpers
    "get_middleware_runtime",
    "set_middleware_runtime",
    "reset_middleware_runtime",
    "get_middleware_provider",
    "set_middleware_provider",
    "reset_middleware_provider",
]
