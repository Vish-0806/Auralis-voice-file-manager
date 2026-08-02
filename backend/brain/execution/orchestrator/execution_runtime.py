"""Execution Runtime for the Auralis Command Execution Orchestrator (Phase 12.3).

Thread-safe singleton lifecycle manager orchestrating the ExecutionProvider.
Manages status transitions, process_command delegation, health monitoring, and statistics.
"""

from enum import Enum
import logging
import threading
from typing import Any, Dict, Optional

from brain.execution.orchestrator.execution_provider import ExecutionProvider
from brain.execution.orchestrator.interfaces import IExecutionRuntime
from brain.execution.orchestrator.orchestrator_models import (
    ExecutionHealth,
    ExecutionResult,
    ExecutionStatistics,
)

logger = logging.getLogger(__name__)


class OrchestratorRuntimeStatus(str, Enum):
    """Lifecycle status states for the Command Execution Orchestrator Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class ExecutionRuntime(IExecutionRuntime):
    """Thread-safe singleton runtime managing the ExecutionProvider lifecycle."""

    def __init__(self, provider: Optional[ExecutionProvider] = None) -> None:
        """Initializes ExecutionRuntime with optional provider instance."""
        self._lock = threading.RLock()
        self._status = OrchestratorRuntimeStatus.INITIALIZING
        self._provider = provider or ExecutionProvider()

    @property
    def status(self) -> OrchestratorRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> ExecutionProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Execution Orchestrator runtime.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == OrchestratorRuntimeStatus.READY:
                return True

            try:
                self._status = OrchestratorRuntimeStatus.READY
                logger.info("Command Execution Orchestrator Runtime Initialized")
                return True
            except Exception as exc:
                self._status = OrchestratorRuntimeStatus.ERROR
                logger.error("ExecutionRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down execution runtime.

        Returns:
            True always.
        """
        with self._lock:
            self._status = OrchestratorRuntimeStatus.SHUTDOWN
            logger.info("Command Execution Orchestrator Runtime Shutdown")
            return True

    def process_command(
        self,
        request_or_prompt: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Process input command through the ExecutionProvider.

        Args:
            request_or_prompt: Raw prompt, IntentResolution, or ExecutionRequest.
            context: Optional contextual parameters.

        Returns:
            Immutable ExecutionResult model.
        """
        with self._lock:
            if self._status in (OrchestratorRuntimeStatus.INITIALIZING, OrchestratorRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = OrchestratorRuntimeStatus.RUNNING

        try:
            return self._provider.execute(request_or_prompt, context=context)
        finally:
            with self._lock:
                if self._status == OrchestratorRuntimeStatus.RUNNING:
                    self._status = prev_status if prev_status != OrchestratorRuntimeStatus.INITIALIZING else OrchestratorRuntimeStatus.READY

    def health_check(self) -> ExecutionHealth:
        """Fetch health check diagnostic status."""
        with self._lock:
            provider_health = self._provider.health_check()
            is_healthy = (self._status in (OrchestratorRuntimeStatus.READY, OrchestratorRuntimeStatus.RUNNING)) and provider_health.healthy

            issues = list(provider_health.detected_issues)
            if self._status == OrchestratorRuntimeStatus.ERROR:
                issues.append("Orchestrator runtime is in ERROR status")

            return ExecutionHealth(
                status=self._status.value if is_healthy else "ERROR",
                healthy=is_healthy,
                components=provider_health.components,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> ExecutionStatistics:
        """Fetch execution statistics snapshot."""
        with self._lock:
            return self._provider.get_statistics()

    def clear(self) -> None:
        """Reset execution statistics and transient state."""
        with self._lock:
            self._provider.clear()
            if self._status != OrchestratorRuntimeStatus.SHUTDOWN:
                self._status = OrchestratorRuntimeStatus.READY
            logger.info("ExecutionRuntime cleared")
