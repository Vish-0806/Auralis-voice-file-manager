"""API Runtime Foundation Package (Phase 15.1).

Provider-independent API Runtime foundation establishing lifecycle, thread-safety,
immutable state models, exception hierarchy, ABC interfaces, provider, runtime,
and singleton accessors.
"""

from backend.application.api.api_provider import ApiProvider
from backend.application.api.api_runtime import ApiRuntime
from backend.application.api.exceptions import (
    ApiConfigurationException,
    ApiInitializationException,
    ApiProviderException,
    ApiRuntimeException,
    ApiValidationException,
)
from backend.application.api.interfaces import IApiProvider, IApiRuntime
from backend.application.api.models import (
    ApiCapabilities,
    ApiConfiguration,
    ApiContext,
    ApiDiagnostics,
    ApiHealth,
    ApiRuntimeState,
    ApiState,
    ApiStatistics,
)
from backend.application.api.runtime import (
    get_api_provider,
    get_api_runtime,
    reset_api_provider,
    reset_api_runtime,
    set_api_provider,
    set_api_runtime,
)

__all__ = [
    # Models & Enums
    "ApiRuntimeState",
    "ApiState",
    "ApiCapabilities",
    "ApiHealth",
    "ApiStatistics",
    "ApiContext",
    "ApiConfiguration",
    "ApiDiagnostics",
    # Exceptions
    "ApiRuntimeException",
    "ApiInitializationException",
    "ApiConfigurationException",
    "ApiProviderException",
    "ApiValidationException",
    # Interfaces
    "IApiRuntime",
    "IApiProvider",
    # Implementations
    "ApiProvider",
    "ApiRuntime",
    # Runtime Helpers
    "get_api_provider",
    "get_api_runtime",
    "reset_api_provider",
    "reset_api_runtime",
    "set_api_provider",
    "set_api_runtime",
]
