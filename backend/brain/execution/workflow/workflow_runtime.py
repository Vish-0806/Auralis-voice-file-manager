"""Workflow Runtime for the Auralis Workflow Execution Engine (Phase 12.4).

Thread-safe singleton lifecycle manager orchestrating the WorkflowProvider.
Manages status transitions, process_workflow delegation, health monitoring, and statistics.
"""

from enum import Enum
import logging
import threading
from typing import Any, Dict, Optional

from brain.execution.workflow.interfaces import IWorkflowRuntime
from brain.execution.workflow.workflow_models import (
    WorkflowHealth,
    WorkflowResult,
    WorkflowStatistics,
)
from brain.execution.workflow.workflow_provider import WorkflowProvider

logger = logging.getLogger(__name__)


class WorkflowRuntimeStatus(str, Enum):
    """Lifecycle status states for the Workflow Execution Engine Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class WorkflowRuntime(IWorkflowRuntime):
    """Thread-safe singleton runtime managing the WorkflowProvider lifecycle."""

    def __init__(self, provider: Optional[WorkflowProvider] = None) -> None:
        """Initializes WorkflowRuntime with optional provider instance."""
        self._lock = threading.RLock()
        self._status = WorkflowRuntimeStatus.INITIALIZING
        self._provider = provider or WorkflowProvider()

    @property
    def status(self) -> WorkflowRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> WorkflowProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Workflow Execution Engine runtime.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == WorkflowRuntimeStatus.READY:
                return True

            try:
                self._status = WorkflowRuntimeStatus.READY
                logger.info("Workflow Execution Engine Runtime Initialized")
                return True
            except Exception as exc:
                self._status = WorkflowRuntimeStatus.ERROR
                logger.error("WorkflowRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down workflow runtime.

        Returns:
            True always.
        """
        with self._lock:
            self._status = WorkflowRuntimeStatus.SHUTDOWN
            logger.info("Workflow Execution Engine Runtime Shutdown")
            return True

    def process_workflow(
        self,
        request_or_steps: Any,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[Dict[str, bool]] = None,
    ) -> WorkflowResult:
        """Process workflow request through the WorkflowProvider.

        Args:
            request_or_steps: WorkflowRequest, List[WorkflowStep], or dict.
            context: Optional contextual parameters.
            cancellation_token: Optional cancellation token dict.

        Returns:
            Immutable WorkflowResult model.
        """
        with self._lock:
            if self._status in (WorkflowRuntimeStatus.INITIALIZING, WorkflowRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = WorkflowRuntimeStatus.RUNNING

        try:
            return self._provider.execute_workflow(
                request_or_steps,
                context=context,
                cancellation_token=cancellation_token,
            )
        finally:
            with self._lock:
                if self._status == WorkflowRuntimeStatus.RUNNING:
                    self._status = prev_status if prev_status != WorkflowRuntimeStatus.INITIALIZING else WorkflowRuntimeStatus.READY

    def health_check(self) -> WorkflowHealth:
        """Fetch health check diagnostic status."""
        with self._lock:
            provider_health = self._provider.health_check()
            is_healthy = (self._status in (WorkflowRuntimeStatus.READY, WorkflowRuntimeStatus.RUNNING)) and provider_health.healthy

            issues = list(provider_health.detected_issues)
            if self._status == WorkflowRuntimeStatus.ERROR:
                issues.append("Workflow runtime is in ERROR status")

            return WorkflowHealth(
                status=self._status.value if is_healthy else "ERROR",
                healthy=is_healthy,
                components=provider_health.components,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> WorkflowStatistics:
        """Fetch workflow execution statistics snapshot."""
        with self._lock:
            return self._provider.get_statistics()

    def clear(self) -> None:
        """Reset workflow statistics and transient state."""
        with self._lock:
            self._provider.clear()
            if self._status != WorkflowRuntimeStatus.SHUTDOWN:
                self._status = WorkflowRuntimeStatus.READY
            logger.info("WorkflowRuntime cleared")
