"""Filesystem Runtime Coordinator for the Auralis Filesystem Engine (Phase 9.5).

Provides singleton lifecycle management, health monitoring, and statistics
aggregation for the Filesystem Engine subsystem.
"""

import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.filesystem.filesystem_models import FilesystemHealth, FilesystemStatistics
from brain.filesystem.filesystem_provider import FilesystemProvider
from brain.filesystem.permission_manager import PermissionManager
from brain.filesystem.file_operations import FileOperations
from brain.filesystem.directory_operations import DirectoryOperations
from brain.filesystem.search_engine import SearchEngine
from brain.filesystem.transaction_manager import TransactionManager
from brain.filesystem.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)


class FilesystemRuntimeStatus(str, Enum):
    """Lifecycle states for the Filesystem Runtime Coordinator."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class _MutableStatistics:
    """Mutable internal statistics accumulator."""

    def __init__(self) -> None:
        self.operations_started: int = 0
        self.operations_completed: int = 0
        self.operations_failed: int = 0
        self.transactions_started: int = 0
        self.transactions_committed: int = 0
        self.transactions_aborted: int = 0
        self.rollbacks_performed: int = 0
        self.bytes_copied: int = 0
        self.bytes_moved: int = 0
        self.bytes_deleted: int = 0
        self.searches_performed: int = 0
        self._total_operation_ms: float = 0.0
        self.peak_concurrent_operations: int = 0
        self._current_concurrent: int = 0

    def snapshot(self) -> FilesystemStatistics:
        avg_ms = (
            self._total_operation_ms / self.operations_completed
            if self.operations_completed > 0
            else 0.0
        )
        return FilesystemStatistics(
            operations_started=self.operations_started,
            operations_completed=self.operations_completed,
            operations_failed=self.operations_failed,
            transactions_started=self.transactions_started,
            transactions_committed=self.transactions_committed,
            transactions_aborted=self.transactions_aborted,
            rollbacks_performed=self.rollbacks_performed,
            bytes_copied=self.bytes_copied,
            bytes_moved=self.bytes_moved,
            bytes_deleted=self.bytes_deleted,
            searches_performed=self.searches_performed,
            average_operation_ms=round(avg_ms, 3),
            peak_concurrent_operations=self.peak_concurrent_operations,
        )


class FilesystemRuntimeCoordinator:
    """Thread-safe singleton coordinator for the Filesystem Engine subsystem.

    Manages the lifecycle of all filesystem components and exposes
    health-check / statistics interfaces.
    """

    _COMPONENTS: List[str] = [
        "PermissionManager",
        "FileOperations",
        "DirectoryOperations",
        "SearchEngine",
        "TransactionManager",
        "RollbackManager",
        "FilesystemProvider",
    ]

    def __init__(
        self,
        provider: Optional[FilesystemProvider] = None,
    ) -> None:
        """Initializes FilesystemRuntimeCoordinator.

        Args:
            provider: Optional pre-built :class:`FilesystemProvider`.  A new
                      one is created during ``initialize()`` if not provided.
        """
        self._lock = threading.RLock()
        self._status: FilesystemRuntimeStatus = FilesystemRuntimeStatus.INITIALIZING
        self._provider: Optional[FilesystemProvider] = provider
        self._stats = _MutableStatistics()
        self._started_at: Optional[datetime] = None
        self._runtime_id: str = f"fs-runtime-{uuid.uuid4().hex[:6]}"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """Initialize all filesystem components and transition to READY.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        with self._lock:
            try:
                self._status = FilesystemRuntimeStatus.INITIALIZING
                if self._provider is None:
                    perm = PermissionManager()
                    file_ops = FileOperations(perm)
                    dir_ops = DirectoryOperations(perm)
                    search = SearchEngine()
                    rollback = RollbackManager()
                    tx_manager = TransactionManager()
                    self._provider = FilesystemProvider(
                        permission_manager=perm,
                        file_ops=file_ops,
                        dir_ops=dir_ops,
                        search_engine=search,
                        transaction_manager=tx_manager,
                        rollback_manager=rollback,
                    )
                    # Wire up the provider as executor
                    tx_manager.set_executor(self._provider._execute_operation)

                self._started_at = datetime.now(timezone.utc)
                self._status = FilesystemRuntimeStatus.READY
                logger.info("Filesystem Initialized: runtime_id=%s", self._runtime_id)
                return True
            except Exception as exc:
                self._status = FilesystemRuntimeStatus.ERROR
                logger.error("FilesystemRuntimeCoordinator.initialize failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Shut down the filesystem runtime and release all component references.

        Returns:
            True always (graceful shutdown).
        """
        with self._lock:
            self._status = FilesystemRuntimeStatus.SHUTDOWN
            self._provider = None
            logger.info("Filesystem Shutdown: runtime_id=%s", self._runtime_id)
            return True

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def health_check(self) -> FilesystemHealth:
        """Return an immutable health snapshot.

        Returns:
            :class:`FilesystemHealth`.
        """
        with self._lock:
            healthy = self._status == FilesystemRuntimeStatus.READY
            uptime = 0.0
            if self._started_at:
                uptime = (datetime.now(timezone.utc) - self._started_at).total_seconds()

            return FilesystemHealth(
                healthy=healthy,
                status=self._status.value,
                registered_components=self._COMPONENTS,
                uptime_seconds=round(uptime, 2),
                checked_at=datetime.now(timezone.utc),
                metadata={
                    "runtime_id": self._runtime_id,
                    "thread_safety": "PROTECTED",
                },
            )

    def get_statistics(self) -> FilesystemStatistics:
        """Return an immutable statistics snapshot.

        Returns:
            :class:`FilesystemStatistics`.
        """
        with self._lock:
            return self._stats.snapshot()

    def clear(self) -> None:
        """Reset all statistics counters to zero."""
        with self._lock:
            self._stats = _MutableStatistics()
            logger.debug("FilesystemRuntimeCoordinator statistics cleared")

    def list_components(self) -> List[str]:
        """Return the list of registered component names.

        Returns:
            List of component name strings.
        """
        return list(self._COMPONENTS)

    # ------------------------------------------------------------------
    # Provider Access
    # ------------------------------------------------------------------

    def get_provider(self) -> FilesystemProvider:
        """Return the active :class:`FilesystemProvider`.

        Auto-initializes if the runtime is in SHUTDOWN state.

        Returns:
            Active :class:`FilesystemProvider`.

        Raises:
            RuntimeError: If initialization fails.
        """
        with self._lock:
            if self._status == FilesystemRuntimeStatus.SHUTDOWN or self._provider is None:
                self.initialize()
            if self._provider is None:
                raise RuntimeError("FilesystemRuntimeCoordinator: provider unavailable")
            return self._provider

    @property
    def status(self) -> FilesystemRuntimeStatus:
        """Current runtime status."""
        with self._lock:
            return self._status

    # ------------------------------------------------------------------
    # Statistics Tracking Helpers (called by provider wrappers)
    # ------------------------------------------------------------------

    def record_operation_start(self) -> None:
        with self._lock:
            self._stats.operations_started += 1
            self._stats._current_concurrent += 1
            if self._stats._current_concurrent > self._stats.peak_concurrent_operations:
                self._stats.peak_concurrent_operations = self._stats._current_concurrent

    def record_operation_complete(self, duration_ms: float = 0.0) -> None:
        with self._lock:
            self._stats.operations_completed += 1
            self._stats._total_operation_ms += duration_ms
            self._stats._current_concurrent = max(0, self._stats._current_concurrent - 1)

    def record_operation_failed(self) -> None:
        with self._lock:
            self._stats.operations_failed += 1
            self._stats._current_concurrent = max(0, self._stats._current_concurrent - 1)

    def record_transaction_started(self) -> None:
        with self._lock:
            self._stats.transactions_started += 1

    def record_transaction_committed(self) -> None:
        with self._lock:
            self._stats.transactions_committed += 1

    def record_transaction_aborted(self) -> None:
        with self._lock:
            self._stats.transactions_aborted += 1

    def record_rollback(self) -> None:
        with self._lock:
            self._stats.rollbacks_performed += 1

    def record_search(self) -> None:
        with self._lock:
            self._stats.searches_performed += 1

    def record_bytes_copied(self, n: int) -> None:
        with self._lock:
            self._stats.bytes_copied += n

    def record_bytes_moved(self, n: int) -> None:
        with self._lock:
            self._stats.bytes_moved += n

    def record_bytes_deleted(self, n: int) -> None:
        with self._lock:
            self._stats.bytes_deleted += n


# ---------------------------------------------------------------------------
# Global Singleton Accessors
# ---------------------------------------------------------------------------

_global_filesystem_runtime: Optional[FilesystemRuntimeCoordinator] = None
_global_filesystem_lock = threading.RLock()


def get_filesystem_runtime() -> FilesystemRuntimeCoordinator:
    """Return (or create) the global Filesystem Runtime singleton.

    Thread-safe.  Automatically initializes the runtime if it does not exist.

    Returns:
        :class:`FilesystemRuntimeCoordinator` singleton instance.
    """
    global _global_filesystem_runtime
    with _global_filesystem_lock:
        if _global_filesystem_runtime is None:
            _global_filesystem_runtime = FilesystemRuntimeCoordinator()
            _global_filesystem_runtime.initialize()
        return _global_filesystem_runtime


def reset_filesystem_runtime() -> None:
    """Reset (destroy) the global Filesystem Runtime singleton.

    The next call to ``get_filesystem_runtime()`` will create a fresh instance.
    Thread-safe.
    """
    global _global_filesystem_runtime
    with _global_filesystem_lock:
        if _global_filesystem_runtime is not None:
            try:
                _global_filesystem_runtime.shutdown()
            except Exception:
                pass
            _global_filesystem_runtime = None
        logger.debug("Filesystem Runtime reset")
