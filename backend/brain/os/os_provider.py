"""Operating System Provider implementation (Phase 11.1).

Aggregates PlatformDetector, EnvironmentService, and PathService into a single unified provider.
Provides health tracking, availability verification, and system diagnostics.
This is strictly an OS abstraction provider, NOT a filesystem provider.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from brain.os.environment_service import EnvironmentService
from brain.os.interfaces import (
    IEnvironmentService,
    IOperatingSystemProvider,
    IPathService,
    IPlatformDetector,
)
from brain.os.os_models import (
    EnvironmentSnapshot,
    OperatingSystemInfo,
    ProviderConfiguration,
    ProviderHealth,
)
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class OperatingSystemProvider(IOperatingSystemProvider):
    """Canonical operating system abstraction provider."""

    def __init__(
        self,
        platform_detector: Optional[IPlatformDetector] = None,
        environment_service: Optional[IEnvironmentService] = None,
        path_service: Optional[IPathService] = None,
        configuration: Optional[ProviderConfiguration] = None,
    ) -> None:
        self._detector = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector
        )
        self._path_service = path_service or PathService(
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._config = configuration or ProviderConfiguration()
        self._registered_at = datetime.now(timezone.utc)
        self._available = True

    def get_platform_info(self) -> OperatingSystemInfo:
        """Return immutable system platform information."""
        return self._detector.detect_system_info()

    def get_environment_snapshot(self) -> EnvironmentSnapshot:
        """Return immutable environment snapshot."""
        return self._env_service.capture_snapshot()

    def get_path_service(self) -> IPathService:
        """Return path service instance."""
        return self._path_service

    def get_health(self) -> ProviderHealth:
        """Return current provider health status."""
        plat_info = self.get_platform_info()
        return ProviderHealth(
            healthy=self._available,
            status="READY" if self._available else "UNAVAILABLE",
            registered_at=self._registered_at,
            last_health_check=datetime.now(timezone.utc),
            details={
                "os": plat_info.operating_system.value,
                "arch": plat_info.architecture.value,
                "hostname": plat_info.hostname,
                "strict_path_validation": self._config.strict_path_validation,
            },
        )

    def is_available(self) -> bool:
        """Return True if provider is ready and available."""
        return self._available

    def set_availability(self, available: bool) -> None:
        """Set availability state (used for resilience and health simulation)."""
        self._available = available

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic metrics and configuration metadata."""
        plat_info = self.get_platform_info()
        arch_info = self._detector.detect_platform_architecture()
        env_snap = self.get_environment_snapshot()

        return {
            "provider_type": "OperatingSystemProvider",
            "available": self._available,
            "operating_system": plat_info.operating_system.value,
            "architecture": plat_info.architecture.value,
            "hostname": plat_info.hostname,
            "python_version": plat_info.python_version,
            "pointer_bitness": arch_info.pointer_bitness,
            "is_64bit": arch_info.is_64bit,
            "username": env_snap.username,
            "pid": env_snap.process_id,
            "registered_at": self._registered_at.isoformat(),
        }
