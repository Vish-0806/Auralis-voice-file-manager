"""Abstract interfaces for the Operating System Abstraction Layer (Phase 11.1).

Defines canonical interfaces for Platform Detection, Environment Services,
Path Services, OS Providers, and OS Runtime components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from brain.os.os_models import (
    Architecture,
    EnvironmentSnapshot,
    OperatingSystem,
    OperatingSystemInfo,
    OSRuntimeStatus,
    PathInformation,
    PlatformArchitecture,
    ProviderHealth,
    RuntimeStatistics,
)


class IPlatformDetector(ABC):
    """Interface for platform identification and hardware detection."""

    @abstractmethod
    def detect_os(self) -> OperatingSystem:
        """Detect the operating system family."""
        pass

    @abstractmethod
    def detect_architecture(self) -> Architecture:
        """Detect the hardware CPU architecture."""
        pass

    @abstractmethod
    def detect_system_info(self) -> OperatingSystemInfo:
        """Gather comprehensive system identification metadata."""
        pass

    @abstractmethod
    def detect_platform_architecture(self) -> PlatformArchitecture:
        """Gather detailed platform architecture metadata."""
        pass


class IEnvironmentService(ABC):
    """Interface for runtime environment inspection and variable management."""

    @abstractmethod
    def get_home_directory(self) -> str:
        """Return user home directory path."""
        pass

    @abstractmethod
    def get_cwd(self) -> str:
        """Return current working directory path."""
        pass

    @abstractmethod
    def get_temp_directory(self) -> str:
        """Return temporary files directory path."""
        pass

    @abstractmethod
    def get_environment_variables(self) -> Dict[str, str]:
        """Return copy of active environment variables."""
        pass

    @abstractmethod
    def get_env_var(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Lookup specific environment variable."""
        pass

    @abstractmethod
    def get_username(self) -> str:
        """Return current user account name."""
        pass

    @abstractmethod
    def get_timezone(self) -> str:
        """Return local system timezone string."""
        pass

    @abstractmethod
    def get_locale(self) -> str:
        """Return current system locale string."""
        pass

    @abstractmethod
    def get_python_executable(self) -> str:
        """Return absolute path to active Python binary."""
        pass

    @abstractmethod
    def get_process_id(self) -> int:
        """Return current process ID."""
        pass

    @abstractmethod
    def capture_snapshot(self) -> EnvironmentSnapshot:
        """Capture an immutable snapshot of current environment state."""
        pass


class IPathService(ABC):
    """Interface for cross-platform path resolution, normalization, and safety check."""

    @abstractmethod
    def normalize_path(self, path: str, target_os: Optional[OperatingSystem] = None) -> str:
        """Normalize slashes, collapse relative components, and strip redundant separators."""
        pass

    @abstractmethod
    def expand_user(self, path: str, home_override: Optional[str] = None) -> str:
        """Expand user home directory tilde (~) notation."""
        pass

    @abstractmethod
    def expand_vars(self, path: str, env_override: Optional[Dict[str, str]] = None) -> str:
        """Expand $VAR, ${VAR}, and %VAR% environment variables."""
        pass

    @abstractmethod
    def resolve_absolute(self, path: str, base_dir: Optional[str] = None) -> str:
        """Resolve path to an absolute path against base_dir or CWD."""
        pass

    @abstractmethod
    def is_safe_path(self, path: str, base_dir: Optional[str] = None) -> bool:
        """Validate whether path stays within base_dir without directory traversal."""
        pass

    @abstractmethod
    def get_separator(self, target_os: Optional[OperatingSystem] = None) -> str:
        """Return directory path separator character for targeted OS."""
        pass

    @abstractmethod
    def compare_paths(
        self, path1: str, path2: str, target_os: Optional[OperatingSystem] = None
    ) -> bool:
        """Compare two paths for logical equality considering target OS case sensitivity."""
        pass

    @abstractmethod
    def get_canonical_path(self, path: str) -> str:
        """Return fully canonicalized absolute path."""
        pass

    @abstractmethod
    def get_path_info(self, path: str) -> PathInformation:
        """Return detailed PathInformation model for a given path."""
        pass


class IOperatingSystemProvider(ABC):
    """Interface for Operating System Abstraction Provider."""

    @abstractmethod
    def get_platform_info(self) -> OperatingSystemInfo:
        """Return immutable system platform information."""
        pass

    @abstractmethod
    def get_environment_snapshot(self) -> EnvironmentSnapshot:
        """Return immutable environment snapshot."""
        pass

    @abstractmethod
    def get_path_service(self) -> IPathService:
        """Return path service instance."""
        pass

    @abstractmethod
    def get_health(self) -> ProviderHealth:
        """Return current provider health status."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if provider is ready and available."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic metrics."""
        pass


class IOperatingSystemRuntime(ABC):
    """Interface for Operating System Runtime lifecycle and manager."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the OS runtime coordinator."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown runtime coordinator."""
        pass

    @abstractmethod
    def register_provider(self, provider: IOperatingSystemProvider) -> None:
        """Register an OS provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[IOperatingSystemProvider]:
        """Get registered OS provider."""
        pass

    @abstractmethod
    def get_statistics(self) -> RuntimeStatistics:
        """Get current runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> OSRuntimeStatus:
        """Get current overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information."""
        pass
