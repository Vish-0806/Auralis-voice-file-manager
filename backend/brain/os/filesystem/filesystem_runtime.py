"""Filesystem Runtime Coordinator (Phase 11.2).

Manages the lifecycle, statistics tracking, health checks, provider registration,
and thread safety for the Filesystem Subsystem using threading.RLock().
Integrates with Phase 11.1 OperatingSystemRuntime.
"""

import threading
import time
from typing import Any, Dict, Optional

from brain.os.filesystem.filesystem_models import (
    FilesystemRuntimeStatus,
    FilesystemStatistics,
)
from brain.os.filesystem.filesystem_provider import FilesystemProvider
from brain.os.filesystem.interfaces import (
    IFilesystemProvider,
    IFilesystemRuntime,
)
from brain.os.os_runtime import OperatingSystemRuntime
from brain.os.runtime import get_os_runtime


class FilesystemRuntime(IFilesystemRuntime):
    """Thread-safe runtime coordinator for the Filesystem Subsystem."""

    def __init__(
        self,
        provider: Optional[IFilesystemProvider] = None,
        os_runtime: Optional[OperatingSystemRuntime] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._os_runtime = os_runtime
        self._state = "Initializing"
        self._start_time: Optional[float] = None

        self._total_ops = 0
        self._reads_count = 0
        self._writes_count = 0
        self._deletes_count = 0
        self._searches_count = 0
        self._bytes_read = 0
        self._bytes_written = 0
        self._errors_count = 0

    def initialize(self) -> None:
        """Initialize filesystem runtime and bind OS runtime."""
        with self._lock:
            if self._state == "Running":
                return

            if self._os_runtime is None:
                self._os_runtime = get_os_runtime()

            if self._provider is None:
                self._provider = FilesystemProvider()

            self._state = "Running"
            self._start_time = time.time()

    def shutdown(self) -> None:
        """Shutdown filesystem runtime."""
        with self._lock:
            self._state = "Stopped"

    def register_provider(self, provider: IFilesystemProvider) -> None:
        """Register filesystem provider."""
        with self._lock:
            if not isinstance(provider, IFilesystemProvider):
                raise TypeError("Provider must implement IFilesystemProvider")
            self._provider = provider

    def get_provider(self) -> Optional[IFilesystemProvider]:
        """Get registered filesystem provider."""
        with self._lock:
            return self._provider

    def record_operation(
        self, op_type: str, bytes_count: int = 0, is_error: bool = False
    ) -> None:
        """Record operation statistics."""
        with self._lock:
            self._total_ops += 1
            if op_type in ("read_text", "read_bytes", "list_dir"):
                self._reads_count += 1
                self._bytes_read += bytes_count
            elif op_type in ("write_text", "write_bytes", "copy_file", "move_file"):
                self._writes_count += 1
                self._bytes_written += bytes_count
            elif op_type == "delete_file":
                self._deletes_count += 1
            elif op_type == "search":
                self._searches_count += 1

            if is_error:
                self._errors_count += 1

    def get_statistics(self) -> FilesystemStatistics:
        """Get runtime performance statistics."""
        with self._lock:
            return FilesystemStatistics(
                total_operations=self._total_ops,
                reads_count=self._reads_count,
                writes_count=self._writes_count,
                deletes_count=self._deletes_count,
                searches_count=self._searches_count,
                bytes_read=self._bytes_read,
                bytes_written=self._bytes_written,
                errors_count=self._errors_count,
                average_latency_ms=0.0,
            )

    def get_health(self) -> FilesystemRuntimeStatus:
        """Get overall runtime health status."""
        with self._lock:
            uptime = 0.0
            if self._start_time is not None and self._state == "Running":
                uptime = max(0.0, time.time() - self._start_time)

            healthy = (
                self._state == "Running"
                and self._provider is not None
                and self._provider.get_health().healthy
            )

            return FilesystemRuntimeStatus(
                state=self._state,
                healthy=healthy,
                provider_registered=self._provider is not None,
                total_operations=self._total_ops,
                errors_count=self._errors_count,
                uptime_seconds=uptime,
            )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostics dictionary."""
        with self._lock:
            health = self.get_health()
            stats = self.get_statistics()
            provider_diag = (
                self._provider.get_diagnostics() if self._provider else {}
            )

            return {
                "runtime_state": self._state,
                "healthy": health.healthy,
                "uptime_seconds": health.uptime_seconds,
                "total_operations": stats.total_operations,
                "errors_count": stats.errors_count,
                "provider_diagnostics": provider_diag,
            }
