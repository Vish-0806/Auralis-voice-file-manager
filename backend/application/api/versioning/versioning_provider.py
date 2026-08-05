"""API Versioning Provider Implementation (Phase 15.6).

Thread-safe versioning provider aggregating VersionRegistry, CompatibilityManager,
and DocumentationManager with full lifecycle management, health monitoring,
statistics tracking, and diagnostic telemetry.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.versioning.compatibility_manager import (
    CompatibilityManager,
)
from backend.application.api.versioning.documentation_manager import (
    DocumentationManager,
)
from backend.application.api.versioning.interfaces import (
    ICompatibilityManager,
    IDocumentationManager,
    IVersionRegistry,
    IVersioningProvider,
)
from backend.application.api.versioning.models import (
    DeprecationState,
    ReleaseChannel,
    VersionCapabilities,
    VersionDiagnostics,
    VersionHealth,
    VersionRuntimeState,
    VersionStatistics,
)
from backend.application.api.versioning.version_registry import VersionRegistry

logger = logging.getLogger(__name__)


class VersioningProvider(IVersioningProvider):
    """Production thread-safe versioning provider aggregating versioning components."""

    def __init__(
        self,
        version_registry: Optional[IVersionRegistry] = None,
        compatibility_manager: Optional[ICompatibilityManager] = None,
        documentation_manager: Optional[IDocumentationManager] = None,
        capabilities: Optional[VersionCapabilities] = None,
    ) -> None:
        """Initialize VersioningProvider using Constructor Dependency Injection.

        Args:
            version_registry: Optional IVersionRegistry implementation instance.
            compatibility_manager: Optional ICompatibilityManager implementation instance.
            documentation_manager: Optional IDocumentationManager implementation instance.
            capabilities: Optional VersionCapabilities instance.
        """
        self._lock = RLock()
        self._version_registry = version_registry or VersionRegistry()
        self._compatibility_manager = (
            compatibility_manager or CompatibilityManager()
        )
        self._documentation_manager = (
            documentation_manager or DocumentationManager()
        )
        self._capabilities = capabilities or VersionCapabilities()

        self._status = VersionRuntimeState.UNINITIALIZED
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(self) -> VersionHealth:
        """Initialize the versioning provider and transition state to READY.

        Returns:
            VersionHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status in (
                VersionRuntimeState.INITIALIZING,
                VersionRuntimeState.READY,
            ):
                return self.health()

            self._status = VersionRuntimeState.INITIALIZING
            logger.info("VersioningProvider transitioning to INITIALIZING state.")

            self._status = VersionRuntimeState.READY
            self._total_initializations += 1
            logger.info("VersioningProvider successfully initialized and READY.")
            return self.health()

    def shutdown(self) -> VersionHealth:
        """Shutdown the versioning provider safely and transition state to STOPPED.

        Returns:
            VersionHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status == VersionRuntimeState.STOPPED:
                return self.health()

            self._status = VersionRuntimeState.STOPPING
            logger.info("VersioningProvider transitioning to STOPPING state.")

            self._status = VersionRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("VersioningProvider successfully stopped.")
            return self.health()

    def restart(self) -> VersionHealth:
        """Restart the versioning provider by shutting down if active, then initializing.

        Returns:
            VersionHealth: Updated health snapshot.
        """
        with self._lock:
            logger.info("VersioningProvider restarting...")
            if self._status != VersionRuntimeState.STOPPED:
                self.shutdown()

            health = self.initialize()
            self._total_restarts += 1
            return health

    def health(self) -> VersionHealth:
        """Get health status evaluation snapshot.

        Returns:
            VersionHealth: Immutable health snapshot.
        """
        with self._lock:
            is_healthy = self._status in (
                VersionRuntimeState.READY,
                VersionRuntimeState.UNINITIALIZED,
            )
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"Versioning provider is in state: {self._status.value}",)

            return VersionHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "versions_count": self._version_registry.count_versions(),
                    "documentation_pages_count": self._documentation_manager.count_pages(),
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> VersionStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            VersionStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            all_versions = self._version_registry.list_versions()
            total_versions = len(all_versions)
            stable_versions = sum(
                1 for v in all_versions if v.channel == ReleaseChannel.STABLE
            )
            deprecated_versions = sum(
                1 for v in all_versions if v.state == DeprecationState.DEPRECATED
            )
            total_doc_pages = self._documentation_manager.count_pages()

            compat_telemetry = {}
            if hasattr(self._compatibility_manager, "get_compatibility_telemetry"):
                compat_telemetry = getattr(
                    self._compatibility_manager, "get_compatibility_telemetry"
                )()

            return VersionStatistics(
                total_versions=total_versions,
                stable_versions=stable_versions,
                deprecated_versions=deprecated_versions,
                total_documentation_pages=total_doc_pages,
                total_compatibility_checks=compat_telemetry.get(
                    "total_compatibility_checks", 0
                ),
                metrics={
                    "total_initializations": float(self._total_initializations),
                    "total_restarts": float(self._total_restarts),
                    "total_shutdowns": float(self._total_shutdowns),
                },
            )

    def capabilities(self) -> VersionCapabilities:
        """Get declared capabilities snapshot.

        Returns:
            VersionCapabilities: Immutable capabilities.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> VersionDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            VersionDiagnostics: Immutable diagnostics.
        """
        with self._lock:
            total_versions = self._version_registry.count_versions()
            total_pages = self._documentation_manager.count_pages()
            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Registered Versions: {total_versions}",
                f"Documentation Pages: {total_pages}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
            )
            return VersionDiagnostics(
                state=self._status,
                registered_versions_count=total_versions,
                documentation_pages_count=total_pages,
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "status": self._status.value,
                    "total_shutdowns": self._total_shutdowns,
                },
            )

    def get_version_registry(self) -> IVersionRegistry:
        """Get encapsulated version registry.

        Returns:
            IVersionRegistry: Version registry.
        """
        with self._lock:
            return self._version_registry

    def get_compatibility_manager(self) -> ICompatibilityManager:
        """Get encapsulated compatibility manager.

        Returns:
            ICompatibilityManager: Compatibility manager.
        """
        with self._lock:
            return self._compatibility_manager

    def get_documentation_manager(self) -> IDocumentationManager:
        """Get encapsulated documentation manager.

        Returns:
            IDocumentationManager: Documentation manager.
        """
        with self._lock:
            return self._documentation_manager
