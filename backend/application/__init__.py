"""Backend Application Package (Phase 14.1).

Package representing the Application Bootstrap Runtime and high-level lifecycle coordinator.
Exposes models, exceptions, interfaces, manager implementations, and global accessors.
"""

from backend.application.application_provider import ApplicationProvider
from backend.application.application_runtime import ApplicationRuntime
from backend.application.bootstrap_manager import BootstrapManager
from backend.application.exceptions import (
    ApplicationBootstrapError,
    ApplicationException,
    ApplicationShutdownError,
    InitializationError,
    RuntimeRegistrationError,
    StartupValidationError,
)
from backend.application.initialization_manager import InitializationManager
from backend.application.interfaces import (
    IApplicationProvider,
    IApplicationRuntime,
    IBootstrapManager,
    IInitializationManager,
    IRuntimeRegistry,
    IStartupValidator,
)
from backend.application.models import (
    ApplicationCapabilities,
    ApplicationConfiguration,
    ApplicationContext,
    ApplicationDiagnostics,
    ApplicationHealth,
    ApplicationLifecycleState,
    ApplicationState,
    ApplicationStatistics,
    RuntimeRegistration,
)
from backend.application.runtime import (
    get_application_provider,
    get_application_runtime,
    reset_application_provider,
    reset_application_runtime,
    set_application_provider,
    set_application_runtime,
)
from backend.application.runtime_registry import RuntimeRegistry
from backend.application.startup_validator import StartupValidator

__all__ = [
    # Models
    "ApplicationLifecycleState",
    "ApplicationState",
    "ApplicationConfiguration",
    "ApplicationCapabilities",
    "ApplicationHealth",
    "ApplicationStatistics",
    "ApplicationContext",
    "RuntimeRegistration",
    "ApplicationDiagnostics",
    # Exceptions
    "ApplicationException",
    "ApplicationBootstrapError",
    "RuntimeRegistrationError",
    "InitializationError",
    "StartupValidationError",
    "ApplicationShutdownError",
    # Interfaces
    "IApplicationRuntime",
    "IApplicationProvider",
    "IBootstrapManager",
    "IRuntimeRegistry",
    "IInitializationManager",
    "IStartupValidator",
    # Implementations
    "BootstrapManager",
    "RuntimeRegistry",
    "InitializationManager",
    "StartupValidator",
    "ApplicationProvider",
    "ApplicationRuntime",
    # Runtime Helpers
    "get_application_runtime",
    "set_application_runtime",
    "reset_application_runtime",
    "get_application_provider",
    "set_application_provider",
    "reset_application_provider",
]
