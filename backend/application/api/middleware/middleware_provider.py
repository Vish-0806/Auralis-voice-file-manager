"""API Middleware Provider Implementation (Phase 15.3).

Thread-safe middleware provider aggregating MiddlewareRegistry, PipelineManager,
and MiddlewareExecutor with full lifecycle management, health monitoring,
statistics tracking, and diagnostic capabilities.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.middleware.interfaces import (
    IMiddlewareExecutor,
    IMiddlewareProvider,
    IMiddlewareRegistry,
    IPipelineManager,
)
from backend.application.api.middleware.middleware_executor import (
    MiddlewareExecutor,
)
from backend.application.api.middleware.middleware_registry import (
    MiddlewareRegistry,
)
from backend.application.api.middleware.models import (
    MiddlewareCapabilities,
    MiddlewareDiagnostics,
    MiddlewareHealth,
    MiddlewareRuntimeState,
    MiddlewareState,
    MiddlewareStatistics,
)
from backend.application.api.middleware.pipeline_manager import PipelineManager

logger = logging.getLogger(__name__)


class MiddlewareProvider(IMiddlewareProvider):
    """Production thread-safe middleware provider aggregating middleware runtime components."""

    def __init__(
        self,
        registry: Optional[IMiddlewareRegistry] = None,
        pipeline_manager: Optional[IPipelineManager] = None,
        executor: Optional[IMiddlewareExecutor] = None,
        capabilities: Optional[MiddlewareCapabilities] = None,
    ) -> None:
        """Initialize MiddlewareProvider using Constructor Dependency Injection.

        Args:
            registry: Optional IMiddlewareRegistry implementation instance.
            pipeline_manager: Optional IPipelineManager implementation instance.
            executor: Optional IMiddlewareExecutor implementation instance.
            capabilities: Optional MiddlewareCapabilities instance.
        """
        self._lock = RLock()
        self._registry = registry or MiddlewareRegistry()
        self._pipeline_manager = pipeline_manager or PipelineManager(
            registry=self._registry
        )
        self._executor = executor or MiddlewareExecutor(
            pipeline_manager=self._pipeline_manager
        )
        self._capabilities = capabilities or MiddlewareCapabilities()

        self._status = MiddlewareRuntimeState.UNINITIALIZED
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(self) -> MiddlewareHealth:
        """Initialize the middleware provider and transition state to READY.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status in (
                MiddlewareRuntimeState.INITIALIZING,
                MiddlewareRuntimeState.READY,
            ):
                return self.health()

            self._status = MiddlewareRuntimeState.INITIALIZING
            logger.info("MiddlewareProvider transitioning to INITIALIZING state.")

            self._status = MiddlewareRuntimeState.READY
            self._total_initializations += 1
            logger.info("MiddlewareProvider successfully initialized and READY.")
            return self.health()

    def shutdown(self) -> MiddlewareHealth:
        """Shutdown the middleware provider safely and transition state to STOPPED.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status == MiddlewareRuntimeState.STOPPED:
                return self.health()

            self._status = MiddlewareRuntimeState.STOPPING
            logger.info("MiddlewareProvider transitioning to STOPPING state.")

            self._status = MiddlewareRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("MiddlewareProvider successfully stopped.")
            return self.health()

    def restart(self) -> MiddlewareHealth:
        """Restart the middleware provider by shutting down if active, then initializing.

        Returns:
            MiddlewareHealth: Updated health snapshot.
        """
        with self._lock:
            logger.info("MiddlewareProvider restarting...")
            if self._status != MiddlewareRuntimeState.STOPPED:
                self.shutdown()

            health = self.initialize()
            self._total_restarts += 1
            return health

    def health(self) -> MiddlewareHealth:
        """Get health status evaluation snapshot.

        Returns:
            MiddlewareHealth: Immutable health snapshot.
        """
        with self._lock:
            is_healthy = self._status in (
                MiddlewareRuntimeState.READY,
                MiddlewareRuntimeState.UNINITIALIZED,
            )
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"Middleware provider is in state: {self._status.value}",)

            return MiddlewareHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "registered_count": self._registry.count(),
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> MiddlewareStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            MiddlewareStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            all_middlewares = self._registry.list_middlewares()
            total_mws = len(all_middlewares)
            enabled_mws = sum(1 for m in all_middlewares if m.state == MiddlewareState.ENABLED)
            disabled_mws = sum(1 for m in all_middlewares if m.state == MiddlewareState.DISABLED)

            exec_stats = {}
            if hasattr(self._executor, "get_execution_statistics"):
                exec_stats = getattr(self._executor, "get_execution_statistics")()

            return MiddlewareStatistics(
                total_middlewares=total_mws,
                enabled_middlewares=enabled_mws,
                disabled_middlewares=disabled_mws,
                total_executions=exec_stats.get("total_executions", 0),
                failed_executions=exec_stats.get("failed_executions", 0),
                metrics={
                    "total_initializations": float(self._total_initializations),
                    "total_restarts": float(self._total_restarts),
                    "total_shutdowns": float(self._total_shutdowns),
                },
            )

    def capabilities(self) -> MiddlewareCapabilities:
        """Get declared capabilities snapshot.

        Returns:
            MiddlewareCapabilities: Immutable capabilities.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> MiddlewareDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            MiddlewareDiagnostics: Immutable diagnostics.
        """
        with self._lock:
            all_middlewares = self._registry.list_middlewares()
            enabled_count = sum(1 for m in all_middlewares if m.state == MiddlewareState.ENABLED)
            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Registered Middlewares: {len(all_middlewares)}",
                f"Enabled Middlewares: {enabled_count}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
            )
            return MiddlewareDiagnostics(
                state=self._status,
                registered_count=len(all_middlewares),
                enabled_count=enabled_count,
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "status": self._status.value,
                    "total_shutdowns": self._total_shutdowns,
                },
            )

    def get_registry(self) -> IMiddlewareRegistry:
        """Get encapsulated middleware registry.

        Returns:
            IMiddlewareRegistry: Middleware registry.
        """
        with self._lock:
            return self._registry

    def get_pipeline_manager(self) -> IPipelineManager:
        """Get encapsulated pipeline manager.

        Returns:
            IPipelineManager: Pipeline manager.
        """
        with self._lock:
            return self._pipeline_manager

    def get_executor(self) -> IMiddlewareExecutor:
        """Get encapsulated middleware executor.

        Returns:
            IMiddlewareExecutor: Middleware executor.
        """
        with self._lock:
            return self._executor
