"""API Integration Provider Implementation (Phase 15.9).

Thread-safe integration provider aggregating ApiGateway, RequestCoordinator,
and ResponseCoordinator with full lifecycle management, health monitoring,
statistics tracking, and diagnostic telemetry.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.integration.api_gateway import ApiGateway
from backend.application.api.integration.interfaces import (
    IApiGateway,
    IIntegrationProvider,
    IRequestCoordinator,
    IResponseCoordinator,
)
from backend.application.api.integration.models import (
    IntegrationCapabilities,
    IntegrationDiagnostics,
    IntegrationHealth,
    IntegrationRuntimeState,
    IntegrationStatistics,
)
from backend.application.api.integration.request_coordinator import (
    RequestCoordinator,
)
from backend.application.api.integration.response_coordinator import (
    ResponseCoordinator,
)

logger = logging.getLogger(__name__)


class IntegrationProvider(IIntegrationProvider):
    """Production thread-safe integration provider aggregating gateway orchestration components."""

    def __init__(
        self,
        api_gateway: Optional[IApiGateway] = None,
        request_coordinator: Optional[IRequestCoordinator] = None,
        response_coordinator: Optional[IResponseCoordinator] = None,
        capabilities: Optional[IntegrationCapabilities] = None,
    ) -> None:
        """Initialize IntegrationProvider using Constructor Dependency Injection.

        Args:
            api_gateway: Optional IApiGateway implementation instance.
            request_coordinator: Optional IRequestCoordinator implementation instance.
            response_coordinator: Optional IResponseCoordinator implementation instance.
            capabilities: Optional IntegrationCapabilities instance.
        """
        self._lock = RLock()
        self._request_coordinator = request_coordinator or RequestCoordinator()
        self._response_coordinator = (
            response_coordinator or ResponseCoordinator()
        )
        self._api_gateway = api_gateway or ApiGateway(
            request_coordinator=self._request_coordinator,
            response_coordinator=self._response_coordinator,
        )
        self._capabilities = capabilities or IntegrationCapabilities()

        self._status = IntegrationRuntimeState.UNINITIALIZED
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(self) -> IntegrationHealth:
        """Initialize the integration provider and transition state to READY.

        Returns:
            IntegrationHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status in (
                IntegrationRuntimeState.INITIALIZING,
                IntegrationRuntimeState.READY,
            ):
                return self.health()

            self._status = IntegrationRuntimeState.INITIALIZING
            logger.info("IntegrationProvider transitioning to INITIALIZING state.")

            self._status = IntegrationRuntimeState.READY
            self._total_initializations += 1
            logger.info("IntegrationProvider successfully initialized and READY.")
            return self.health()

    def shutdown(self) -> IntegrationHealth:
        """Shutdown the integration provider safely and transition state to STOPPED.

        Returns:
            IntegrationHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status == IntegrationRuntimeState.STOPPED:
                return self.health()

            self._status = IntegrationRuntimeState.STOPPING
            logger.info("IntegrationProvider transitioning to STOPPING state.")

            self._status = IntegrationRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("IntegrationProvider successfully stopped.")
            return self.health()

    def restart(self) -> IntegrationHealth:
        """Restart the integration provider by shutting down if active, then initializing.

        Returns:
            IntegrationHealth: Updated health snapshot.
        """
        with self._lock:
            logger.info("IntegrationProvider restarting...")
            if self._status != IntegrationRuntimeState.STOPPED:
                self.shutdown()

            health = self.initialize()
            self._total_restarts += 1
            return health

    def health(self) -> IntegrationHealth:
        """Get health status evaluation snapshot.

        Returns:
            IntegrationHealth: Immutable health snapshot.
        """
        with self._lock:
            is_healthy = self._status in (
                IntegrationRuntimeState.READY,
                IntegrationRuntimeState.UNINITIALIZED,
            )
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"Integration provider is in state: {self._status.value}",)

            stats = self._api_gateway.get_gateway_statistics()
            return IntegrationHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "processed_requests": stats.total_requests_processed,
                    "successful_requests": stats.successful_requests,
                    "failed_requests": stats.failed_requests,
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> IntegrationStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            IntegrationStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            gateway_stats = self._api_gateway.get_gateway_statistics()
            return IntegrationStatistics(
                total_requests_processed=gateway_stats.total_requests_processed,
                successful_requests=gateway_stats.successful_requests,
                failed_requests=gateway_stats.failed_requests,
                total_pipeline_executions=gateway_stats.total_pipeline_executions,
                metrics={
                    "total_initializations": float(self._total_initializations),
                    "total_restarts": float(self._total_restarts),
                    "total_shutdowns": float(self._total_shutdowns),
                },
            )

    def capabilities(self) -> IntegrationCapabilities:
        """Get declared capabilities snapshot.

        Returns:
            IntegrationCapabilities: Immutable capabilities.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> IntegrationDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            IntegrationDiagnostics: Immutable diagnostics.
        """
        with self._lock:
            stats = self._api_gateway.get_gateway_statistics()
            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Processed Requests: {stats.total_requests_processed}",
                f"Successful Requests: {stats.successful_requests}",
                f"Failed Requests: {stats.failed_requests}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
            )
            return IntegrationDiagnostics(
                state=self._status,
                active_gateways_count=1,
                processed_requests_count=stats.total_requests_processed,
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "status": self._status.value,
                    "total_shutdowns": self._total_shutdowns,
                },
            )

    def get_api_gateway(self) -> IApiGateway:
        """Get encapsulated API gateway.

        Returns:
            IApiGateway: API gateway.
        """
        with self._lock:
            return self._api_gateway

    def get_request_coordinator(self) -> IRequestCoordinator:
        """Get encapsulated request coordinator.

        Returns:
            IRequestCoordinator: Request coordinator.
        """
        with self._lock:
            return self._request_coordinator

    def get_response_coordinator(self) -> IResponseCoordinator:
        """Get encapsulated response coordinator.

        Returns:
            IResponseCoordinator: Response coordinator.
        """
        with self._lock:
            return self._response_coordinator
