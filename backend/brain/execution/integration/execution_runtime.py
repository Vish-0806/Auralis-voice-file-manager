"""Execution Runtime for the Auralis Execution Runtime Integration (Phase 12.9).

Thread-safe singleton lifecycle manager orchestrating the ExecutionProvider.
Manages status transitions, request processing, health monitoring, and aggregate statistics.
"""

from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.execution.integration.interfaces import IIntegrationRuntime
from brain.execution.integration.execution_provider import ExecutionProvider
from brain.execution.integration.integration_models import (
    ExecutionCapability,
    ExecutionTarget,
    IntegrationHealth,
    IntegrationRequest,
    IntegrationResponse,
    IntegrationStatistics,
)

logger = logging.getLogger(__name__)


class ExecutionRuntimeStatus(str, Enum):
    """Lifecycle status states for the integrated Execution Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class ExecutionRuntime(IIntegrationRuntime):
    """Thread-safe singleton runtime managing the ExecutionProvider lifecycle."""

    def __init__(self, provider: Optional[ExecutionProvider] = None) -> None:
        """Initializes ExecutionRuntime with optional provider instance."""
        self._lock = threading.RLock()
        self._status = ExecutionRuntimeStatus.INITIALIZING
        self._provider = provider or ExecutionProvider()

    @property
    def status(self) -> ExecutionRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> ExecutionProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Execution Integration Runtime.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == ExecutionRuntimeStatus.READY:
                return True

            try:
                self._status = ExecutionRuntimeStatus.READY
                logger.info("Execution Integration Runtime Initialized")
                return True
            except Exception as exc:
                self._status = ExecutionRuntimeStatus.ERROR
                logger.error("ExecutionRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down integration runtime.

        Returns:
            True always.
        """
        with self._lock:
            self._status = ExecutionRuntimeStatus.SHUTDOWN
            logger.info("Execution Integration Runtime Shutdown")
            return True

    def register_capability(
        self,
        name: str,
        target: ExecutionTarget,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCapability:
        """Register capability through provider."""
        return self._provider.register_capability(
            name=name,
            target=target,
            enabled=enabled,
            metadata=metadata,
        )

    def list_capabilities(self, target: Optional[ExecutionTarget] = None) -> List[ExecutionCapability]:
        """List capabilities through provider."""
        return self._provider.list_capabilities(target=target)

    def process_request(self, request: IntegrationRequest) -> IntegrationResponse:
        """Process integration request through provider."""
        with self._lock:
            if self._status in (ExecutionRuntimeStatus.INITIALIZING, ExecutionRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = ExecutionRuntimeStatus.EXECUTING

        try:
            return self._provider.process_request(request)
        finally:
            with self._lock:
                if self._status == ExecutionRuntimeStatus.EXECUTING:
                    self._status = prev_status if prev_status != ExecutionRuntimeStatus.INITIALIZING else ExecutionRuntimeStatus.READY

    def health_check(self) -> IntegrationHealth:
        """Fetch health check diagnostic status."""
        with self._lock:
            provider_health = self._provider.health_check()
            is_healthy = (self._status in (ExecutionRuntimeStatus.READY, ExecutionRuntimeStatus.EXECUTING)) and provider_health.healthy

            issues = list(provider_health.detected_issues)
            if self._status == ExecutionRuntimeStatus.ERROR:
                issues.append("Execution runtime is in ERROR status")

            return IntegrationHealth(
                status=self._status.value if is_healthy else "ERROR",
                healthy=is_healthy,
                subsystems=provider_health.subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> IntegrationStatistics:
        """Fetch integration statistics snapshot."""
        with self._lock:
            return self._provider.get_statistics()

    def clear(self) -> None:
        """Reset integration statistics and transient state."""
        with self._lock:
            self._provider.clear()
            if self._status != ExecutionRuntimeStatus.SHUTDOWN:
                self._status = ExecutionRuntimeStatus.READY
            logger.info("ExecutionRuntime cleared")
