"""Application Subsystem for Auralis Operating System Abstraction (Phase 11.3).

Exports domain models, enums, exceptions, abstract interfaces, services,
provider, runtime coordinator, and singleton accessors.
"""

from brain.os.application.application_detector import ApplicationDetector
from brain.os.application.application_models import (
    ApplicationCapabilities,
    ApplicationHealth,
    ApplicationInfo,
    ApplicationLaunchRequest,
    ApplicationLaunchResult,
    ApplicationRegistryEntry,
    ApplicationRuntimeStatus,
    ApplicationState,
    ApplicationStatistics,
    InstalledApplication,
    LaunchMode,
    RunningApplication,
    VisibilityMode,
)
from brain.os.application.application_monitor import ApplicationMonitor
from brain.os.application.application_provider import ApplicationProvider
from brain.os.application.application_registry import ApplicationRegistry
from brain.os.application.application_runtime import ApplicationRuntime
from brain.os.application.exceptions import (
    ApplicationException,
    ApplicationExecutionError,
    ApplicationLaunchError,
    ApplicationNotFoundError,
    ApplicationRegistryError,
)
from brain.os.application.interfaces import (
    IApplicationDetector,
    IApplicationMonitor,
    IApplicationProvider,
    IApplicationRegistry,
    IApplicationRuntime,
    ILauncherService,
)
from brain.os.application.launcher_service import LauncherService
from brain.os.application.runtime import get_application_runtime, reset_application_runtime

__all__ = [
    # Enums
    "ApplicationState",
    "LaunchMode",
    "VisibilityMode",
    # Models
    "ApplicationInfo",
    "InstalledApplication",
    "RunningApplication",
    "ApplicationLaunchRequest",
    "ApplicationLaunchResult",
    "ApplicationStatistics",
    "ApplicationCapabilities",
    "ApplicationHealth",
    "ApplicationRuntimeStatus",
    "ApplicationRegistryEntry",
    # Exceptions
    "ApplicationException",
    "ApplicationNotFoundError",
    "ApplicationLaunchError",
    "ApplicationRegistryError",
    "ApplicationExecutionError",
    # Interfaces
    "IApplicationRegistry",
    "IApplicationDetector",
    "ILauncherService",
    "IApplicationMonitor",
    "IApplicationProvider",
    "IApplicationRuntime",
    # Implementations & Services
    "ApplicationRegistry",
    "ApplicationDetector",
    "LauncherService",
    "ApplicationMonitor",
    "ApplicationProvider",
    "ApplicationRuntime",
    # Singleton Accessors
    "get_application_runtime",
    "reset_application_runtime",
]
