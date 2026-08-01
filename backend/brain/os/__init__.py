"""Operating System Abstraction Layer for Auralis (Phase 11.1).

Exports canonical enums, immutable Pydantic v2 models, interfaces, platform detector,
environment service, path service, OS provider, OS runtime coordinator, and singleton accessors.
"""

from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import (
    IEnvironmentService,
    IOperatingSystemProvider,
    IOperatingSystemRuntime,
    IPathService,
    IPlatformDetector,
)
from brain.os.os_models import (
    Architecture,
    EnvironmentSnapshot,
    OperatingSystem,
    OperatingSystemInfo,
    OSRuntimeStatus,
    PathInformation,
    PlatformArchitecture,
    ProviderConfiguration,
    ProviderHealth,
    RuntimeState,
    RuntimeStatistics,
)
from brain.os.os_provider import OperatingSystemProvider
from brain.os.os_runtime import OperatingSystemRuntime
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector
from brain.os.runtime import get_os_runtime, reset_os_runtime

__all__ = [
    # Enums
    "OperatingSystem",
    "Architecture",
    "RuntimeState",
    # Models
    "OperatingSystemInfo",
    "PlatformArchitecture",
    "EnvironmentSnapshot",
    "PathInformation",
    "RuntimeStatistics",
    "ProviderHealth",
    "OSRuntimeStatus",
    "ProviderConfiguration",
    # Interfaces
    "IPlatformDetector",
    "IEnvironmentService",
    "IPathService",
    "IOperatingSystemProvider",
    "IOperatingSystemRuntime",
    # Implementations
    "PlatformDetector",
    "EnvironmentService",
    "PathService",
    "OperatingSystemProvider",
    "OperatingSystemRuntime",
    # Runtime Accessors
    "get_os_runtime",
    "reset_os_runtime",
]
