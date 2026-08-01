"""Filesystem Provider implementation (Phase 11.2).

Aggregates PermissionService, MetadataService, DirectoryService, FileService,
FilesystemSearchService, and FilesystemTransactionRuntime into a unified provider.
Provides health tracking, statistics, capabilities, and diagnostics.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional

from brain.os.environment_service import EnvironmentService
from brain.os.filesystem.directory_service import DirectoryService
from brain.os.filesystem.file_service import FileService
from brain.os.filesystem.filesystem_models import (
    FilesystemCapabilities,
    FilesystemHealth,
    FilesystemStatistics,
)
from brain.os.filesystem.interfaces import (
    IDirectoryService,
    IFileService,
    IFilesystemProvider,
    IFilesystemSearchService,
    IFilesystemTransactionRuntime,
    IMetadataService,
    IPermissionService,
)
from brain.os.filesystem.metadata_service import MetadataService
from brain.os.filesystem.permission_service import PermissionService
from brain.os.filesystem.search_service import FilesystemSearchService
from brain.os.filesystem.transaction_runtime import FilesystemTransactionRuntime
from brain.os.interfaces import IEnvironmentService, IPathService, IPlatformDetector
from brain.os.os_models import OperatingSystem
from brain.os.path_service import PathService
from brain.os.platform_detector import PlatformDetector


class FilesystemProvider(IFilesystemProvider):
    """Canonical filesystem subsystem provider."""

    def __init__(
        self,
        permission_service: Optional[IPermissionService] = None,
        metadata_service: Optional[IMetadataService] = None,
        directory_service: Optional[IDirectoryService] = None,
        file_service: Optional[IFileService] = None,
        search_service: Optional[IFilesystemSearchService] = None,
        transaction_runtime: Optional[IFilesystemTransactionRuntime] = None,
        path_service: Optional[IPathService] = None,
        environment_service: Optional[IEnvironmentService] = None,
        platform_detector: Optional[IPlatformDetector] = None,
    ) -> None:
        self._detector = platform_detector or PlatformDetector()
        self._env_service = environment_service or EnvironmentService(
            platform_detector=self._detector
        )
        self._path_service = path_service or PathService(
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._permission_service = permission_service or PermissionService(
            path_service=self._path_service,
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._metadata_service = metadata_service or MetadataService(
            path_service=self._path_service,
            permission_service=self._permission_service,
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._directory_service = directory_service or DirectoryService(
            path_service=self._path_service,
            metadata_service=self._metadata_service,
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._file_service = file_service or FileService(
            path_service=self._path_service,
            permission_service=self._permission_service,
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._search_service = search_service or FilesystemSearchService(
            path_service=self._path_service,
            directory_service=self._directory_service,
            metadata_service=self._metadata_service,
            environment_service=self._env_service,
            platform_detector=self._detector,
        )
        self._transaction_runtime = transaction_runtime or FilesystemTransactionRuntime()

        self._created_at = datetime.now(timezone.utc)
        self._start_time = time.time()
        self._healthy = True

    def get_permission_service(self) -> IPermissionService:
        """Return permission inspection service."""
        return self._permission_service

    def get_metadata_service(self) -> IMetadataService:
        """Return metadata service."""
        return self._metadata_service

    def get_directory_service(self) -> IDirectoryService:
        """Return directory service."""
        return self._directory_service

    def get_file_service(self) -> IFileService:
        """Return file service."""
        return self._file_service

    def get_search_service(self) -> IFilesystemSearchService:
        """Return search service."""
        return self._search_service

    def get_transaction_runtime(self) -> IFilesystemTransactionRuntime:
        """Return transaction runtime."""
        return self._transaction_runtime

    def get_health(self) -> FilesystemHealth:
        """Return provider health status."""
        uptime = max(0.0, time.time() - self._start_time)
        return FilesystemHealth(
            healthy=self._healthy,
            status="READY" if self._healthy else "DEGRADED",
            components={
                "permission_service": self._permission_service is not None,
                "metadata_service": self._metadata_service is not None,
                "directory_service": self._directory_service is not None,
                "file_service": self._file_service is not None,
                "search_service": self._search_service is not None,
                "transaction_runtime": self._transaction_runtime is not None,
            },
            uptime_seconds=uptime,
            details={"provider_type": "FilesystemProvider"},
        )

    def get_statistics(self) -> FilesystemStatistics:
        """Return provider statistics."""
        return FilesystemStatistics()

    def get_capabilities(self) -> FilesystemCapabilities:
        """Return underlying filesystem capabilities."""
        target_os = self._detector.detect_os()
        is_posix = target_os in (OperatingSystem.LINUX, OperatingSystem.MACOS)

        return FilesystemCapabilities(
            supports_symlinks=True,
            supports_permissions=True,
            supports_transactions=True,
            supports_atomic_writes=True,
            supports_posix_permissions=is_posix,
            max_path_length=260 if target_os == OperatingSystem.WINDOWS else 4096,
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic metrics."""
        health = self.get_health()
        caps = self.get_capabilities()

        return {
            "provider_type": "FilesystemProvider",
            "healthy": health.healthy,
            "status": health.status,
            "uptime_seconds": health.uptime_seconds,
            "supports_posix_permissions": caps.supports_posix_permissions,
            "supports_atomic_writes": caps.supports_atomic_writes,
            "created_at": self._created_at.isoformat(),
        }
