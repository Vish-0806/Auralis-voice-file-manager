"""Abstract interfaces for Application Subsystem (Phase 11.3).

Defines canonical interfaces for Application Registry, Detector, Launcher Service,
Monitor, Provider, and Runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.os.application.application_models import (
    ApplicationCapabilities,
    ApplicationHealth,
    ApplicationLaunchRequest,
    ApplicationLaunchResult,
    ApplicationRegistryEntry,
    ApplicationRuntimeStatus,
    ApplicationStatistics,
    InstalledApplication,
    RunningApplication,
)


class IApplicationRegistry(ABC):
    """Interface for registering, looking up, and caching application metadata."""

    @abstractmethod
    def register_application(self, app: InstalledApplication) -> ApplicationRegistryEntry:
        """Register or update an application in the registry."""
        pass

    @abstractmethod
    def unregister_application(self, app_id_or_name: str) -> bool:
        """Remove an application from the registry."""
        pass

    @abstractmethod
    def get_application(self, app_id_or_name: str) -> Optional[InstalledApplication]:
        """Lookup an application by ID or primary name."""
        pass

    @abstractmethod
    def get_by_executable(self, executable_path: str) -> Optional[InstalledApplication]:
        """Lookup an application by executable path."""
        pass

    @abstractmethod
    def get_by_alias(self, alias: str) -> Optional[InstalledApplication]:
        """Lookup an application by alias."""
        pass

    @abstractmethod
    def list_applications(self, category: Optional[str] = None) -> List[InstalledApplication]:
        """List all registered applications, optionally filtered by category."""
        pass


class IApplicationDetector(ABC):
    """Interface for platform-independent desktop application discovery."""

    @abstractmethod
    def detect_installed_applications(self) -> List[InstalledApplication]:
        """Discover installed desktop applications on the host platform."""
        pass

    @abstractmethod
    def find_executable(self, name_or_alias: str) -> Optional[str]:
        """Resolve executable path for an application name or alias."""
        pass

    @abstractmethod
    def is_installed(self, name_or_alias: str) -> bool:
        """Check if an application is installed on the host OS."""
        pass


class ILauncherService(ABC):
    """Interface for launching desktop applications securely."""

    @abstractmethod
    def launch(self, request: ApplicationLaunchRequest) -> ApplicationLaunchResult:
        """Launch an application given a launch specification request."""
        pass

    @abstractmethod
    def launch_executable(
        self,
        executable_path: str,
        arguments: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
    ) -> ApplicationLaunchResult:
        """Directly launch an executable file with arguments."""
        pass


class IApplicationMonitor(ABC):
    """Interface for tracking active launched application processes."""

    @abstractmethod
    def register_process(
        self, process_id: int, app_id: str, executable_path: str, name: str
    ) -> RunningApplication:
        """Register a launched application process for monitoring."""
        pass

    @abstractmethod
    def unregister_process(self, process_id: int) -> bool:
        """Remove a process from active monitoring."""
        pass

    @abstractmethod
    def get_running_applications(self) -> List[RunningApplication]:
        """Get list of all currently tracked running applications."""
        pass

    @abstractmethod
    def get_running_application(self, process_id: int) -> Optional[RunningApplication]:
        """Get details for a specific running process ID."""
        pass

    @abstractmethod
    def get_statistics(self) -> ApplicationStatistics:
        """Get application launch and performance statistics."""
        pass


class IApplicationProvider(ABC):
    """Interface for Application Subsystem Provider."""

    @abstractmethod
    def get_registry(self) -> IApplicationRegistry:
        """Return application registry."""
        pass

    @abstractmethod
    def get_detector(self) -> IApplicationDetector:
        """Return application detector."""
        pass

    @abstractmethod
    def get_launcher(self) -> ILauncherService:
        """Return launcher service."""
        pass

    @abstractmethod
    def get_monitor(self) -> IApplicationMonitor:
        """Return application monitor."""
        pass

    @abstractmethod
    def get_health(self) -> ApplicationHealth:
        """Return provider health status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ApplicationStatistics:
        """Return provider statistics."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ApplicationCapabilities:
        """Return application capabilities."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        pass


class IApplicationRuntime(ABC):
    """Interface for Application Runtime coordinator."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize application runtime."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown application runtime."""
        pass

    @abstractmethod
    def register_provider(self, provider: IApplicationProvider) -> None:
        """Register application provider."""
        pass

    @abstractmethod
    def get_provider(self) -> Optional[IApplicationProvider]:
        """Get registered application provider."""
        pass

    @abstractmethod
    def get_statistics(self) -> ApplicationStatistics:
        """Get application runtime performance statistics."""
        pass

    @abstractmethod
    def get_health(self) -> ApplicationRuntimeStatus:
        """Get overall runtime health status."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get runtime diagnostics dictionary."""
        pass
