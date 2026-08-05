"""API Provider Implementation (Phase 15.1).

Thread-safe, provider-independent API Provider encapsulating state, capabilities,
health metrics, statistics, and diagnostic telemetry without external dependencies.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.exceptions import (
    ApiInitializationException,
)
from backend.application.api.interfaces import IApiProvider
from backend.application.api.models import (
    ApiCapabilities,
    ApiConfiguration,
    ApiContext,
    ApiDiagnostics,
    ApiHealth,
    ApiRuntimeState,
    ApiState,
    ApiStatistics,
)

logger = logging.getLogger(__name__)


class ApiProvider(IApiProvider):
    """Thread-safe API provider implementing provider-independent lifecycle operations."""

    def __init__(
        self,
        config: Optional[ApiConfiguration] = None,
        capabilities: Optional[ApiCapabilities] = None,
        context: Optional[ApiContext] = None,
    ) -> None:
        """Initialize ApiProvider using Constructor Dependency Injection.

        Args:
            config: Optional API configuration instance.
            capabilities: Optional API capabilities instance.
            context: Optional API execution context instance.
        """
        self._lock = RLock()
        self._config = config or ApiConfiguration()
        self._capabilities = capabilities or ApiCapabilities()
        self._context = context or ApiContext()

        self._status = ApiRuntimeState.UNINITIALIZED
        self._initialized_at: Optional[datetime] = None
        self._stopped_at: Optional[datetime] = None
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(
        self, config: Optional[ApiConfiguration] = None
    ) -> ApiState:
        """Initialize the API provider and transition state to READY.

        Args:
            config: Optional configuration override.

        Returns:
            ApiState: Immutable updated state snapshot.

        Raises:
            ApiInitializationException: If provider is in an invalid state for initialization.
        """
        with self._lock:
            if config is not None:
                self._config = config

            if self._status in (ApiRuntimeState.INITIALIZING, ApiRuntimeState.READY):
                return self._get_state_snapshot()

            if self._status == ApiRuntimeState.STOPPING:
                raise ApiInitializationException("Cannot initialize while provider is stopping.")

            self._status = ApiRuntimeState.INITIALIZING
            logger.info("ApiProvider transitioning state to INITIALIZING.")

            now = datetime.now(timezone.utc)
            self._initialized_at = now
            self._stopped_at = None
            self._status = ApiRuntimeState.READY
            self._total_initializations += 1
            logger.info("ApiProvider successfully initialized and READY.")

            return self._get_state_snapshot()

    def shutdown(self) -> ApiState:
        """Shutdown the API provider safely and transition state to STOPPED.

        Returns:
            ApiState: Immutable updated state snapshot.
        """
        with self._lock:
            if self._status == ApiRuntimeState.STOPPED:
                return self._get_state_snapshot()

            self._status = ApiRuntimeState.STOPPING
            logger.info("ApiProvider transitioning state to STOPPING.")

            now = datetime.now(timezone.utc)
            self._stopped_at = now
            self._status = ApiRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("ApiProvider successfully stopped.")

            return self._get_state_snapshot()

    def restart(
        self, config: Optional[ApiConfiguration] = None
    ) -> ApiState:
        """Restart the API provider by stopping if active, then re-initializing.

        Args:
            config: Optional configuration override.

        Returns:
            ApiState: Immutable updated state snapshot.
        """
        with self._lock:
            logger.info("ApiProvider restarting...")
            if self._status != ApiRuntimeState.STOPPED:
                self.shutdown()

            if config is not None:
                self._config = config

            state = self.initialize()
            self._total_restarts += 1
            return state

    def health(self) -> ApiHealth:
        """Get health status evaluation snapshot.

        Returns:
            ApiHealth: Immutable health metrics snapshot.
        """
        with self._lock:
            is_healthy = self._status in (ApiRuntimeState.READY, ApiRuntimeState.UNINITIALIZED)
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"Provider is in state: {self._status.value}",)

            return ApiHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "title": self._config.title,
                    "version": self._config.version,
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ApiStatistics:
        """Get aggregate metrics and usage statistics.

        Returns:
            ApiStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            uptime = self._calculate_uptime()
            return ApiStatistics(
                total_initializations=self._total_initializations,
                total_restarts=self._total_restarts,
                total_shutdowns=self._total_shutdowns,
                active_time_seconds=uptime,
                metrics={
                    "uptime_seconds": uptime,
                    "status_code": 1.0 if self._status == ApiRuntimeState.READY else 0.0,
                },
            )

    def capabilities(self) -> ApiCapabilities:
        """Get declared provider capabilities.

        Returns:
            ApiCapabilities: Immutable capabilities snapshot.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> ApiDiagnostics:
        """Get diagnostic information and telemetry.

        Returns:
            ApiDiagnostics: Immutable diagnostic snapshot.
        """
        with self._lock:
            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
                f"Shutdowns: {self._total_shutdowns}",
            )
            return ApiDiagnostics(
                state=self._status,
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "environment": self._context.environment,
                    "api_id": self._context.api_id,
                    "config_title": self._config.title,
                },
            )

    def _get_state_snapshot(self) -> ApiState:
        """Internal helper to construct an ApiState snapshot under lock."""
        uptime = self._calculate_uptime()
        is_active = self._status == ApiRuntimeState.READY
        is_healthy = self._status in (ApiRuntimeState.READY, ApiRuntimeState.UNINITIALIZED)

        return ApiState(
            status=self._status,
            is_active=is_active,
            is_healthy=is_healthy,
            initialized_at=self._initialized_at,
            stopped_at=self._stopped_at,
            uptime_seconds=uptime,
            metadata={
                "title": self._config.title,
                "version": self._config.version,
            },
        )

    def _calculate_uptime(self) -> float:
        """Internal helper to compute active uptime seconds under lock."""
        if self._initialized_at is None:
            return 0.0
        end_time = self._stopped_at or datetime.now(timezone.utc)
        delta = (end_time - self._initialized_at).total_seconds()
        return max(0.0, delta)
