"""Configuration Package Exports (Phase 14.3.2).

Package exports for models, exceptions, interfaces, configuration sources,
source registry, source manager, configuration provider, configuration runtime, and lazy singleton accessors.
"""

from backend.application.config.configuration_provider import ConfigurationProvider
from backend.application.config.configuration_runtime import ConfigurationRuntime
from backend.application.config.configuration_source_manager import ConfigurationSourceManager
from backend.application.config.dotenv_source import DotEnvConfigurationSource
from backend.application.config.environment_source import EnvironmentConfigurationSource
from backend.application.config.exceptions import (
    ConfigurationException,
    ConfigurationInitializationError,
    ConfigurationProfileError,
    ConfigurationProviderError,
    ConfigurationSourceError,
    ConfigurationValidationError,
)
from backend.application.config.interfaces import (
    IConfigurationDiagnostics,
    IConfigurationManager,
    IConfigurationProvider,
    IConfigurationRuntime,
    IConfigurationSource,
    IConfigurationValidator,
)
from backend.application.config.memory_source import MemoryConfigurationSource
from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationEntry,
    ConfigurationHealth,
    ConfigurationProfile,
    ConfigurationProfileType,
    ConfigurationRuntimeState,
    ConfigurationSnapshot,
    ConfigurationSource,
    ConfigurationSourceType,
    ConfigurationState,
    ConfigurationStatistics,
    SourceHealth,
    SourcePriority,
    SourceRegistration,
    SourceStatistics,
)
from backend.application.config.runtime import (
    get_configuration_provider,
    get_configuration_runtime,
    reset_configuration_provider,
    reset_configuration_runtime,
    set_configuration_provider,
    set_configuration_runtime,
)
from backend.application.config.source_registry import SourceRegistry

__all__ = [
    "ConfigurationRuntimeState",
    "ConfigurationSourceType",
    "ConfigurationProfileType",
    "SourcePriority",
    "ConfigurationState",
    "ConfigurationCapabilities",
    "ConfigurationHealth",
    "ConfigurationStatistics",
    "ConfigurationContext",
    "ConfigurationProfile",
    "ConfigurationSource",
    "SourceRegistration",
    "SourceStatistics",
    "SourceHealth",
    "ConfigurationEntry",
    "ConfigurationSnapshot",
    "ConfigurationDiagnostics",
    "ConfigurationException",
    "ConfigurationInitializationError",
    "ConfigurationValidationError",
    "ConfigurationProviderError",
    "ConfigurationProfileError",
    "ConfigurationSourceError",
    "IConfigurationSource",
    "IConfigurationDiagnostics",
    "IConfigurationValidator",
    "IConfigurationManager",
    "IConfigurationProvider",
    "IConfigurationRuntime",
    "MemoryConfigurationSource",
    "EnvironmentConfigurationSource",
    "DotEnvConfigurationSource",
    "SourceRegistry",
    "ConfigurationSourceManager",
    "ConfigurationProvider",
    "ConfigurationRuntime",
    "get_configuration_runtime",
    "set_configuration_runtime",
    "reset_configuration_runtime",
    "get_configuration_provider",
    "set_configuration_provider",
    "reset_configuration_provider",
]
