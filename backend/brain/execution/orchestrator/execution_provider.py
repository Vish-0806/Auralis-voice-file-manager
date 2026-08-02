"""Execution Provider for the Auralis Command Execution Orchestrator (Phase 12.3).

Aggregates Coordinator, Router, Tracker, and Orchestrator into a unified, thread-safe gateway provider.
Provides end-to-end command orchestration, health monitoring, and statistics diagnostics.
"""

import logging
import threading
from typing import Any, Dict, Optional

from brain.execution.orchestrator.execution_coordinator import ExecutionCoordinator
from brain.execution.orchestrator.execution_orchestrator import ExecutionOrchestrator
from brain.execution.orchestrator.execution_router import ExecutionRouter
from brain.execution.orchestrator.execution_tracker import ExecutionTracker
from brain.execution.orchestrator.interfaces import (
    IExecutionCoordinator,
    IExecutionOrchestrator,
    IExecutionProvider,
    IExecutionRouter,
    IExecutionTracker,
)
from brain.execution.orchestrator.orchestrator_models import (
    ExecutionHealth,
    ExecutionResult,
    ExecutionStatistics,
)

logger = logging.getLogger(__name__)


class ExecutionProvider(IExecutionProvider):
    """Thread-safe provider aggregating coordinator, router, tracker, and orchestrator."""

    def __init__(
        self,
        coordinator: Optional[IExecutionCoordinator] = None,
        router: Optional[IExecutionRouter] = None,
        tracker: Optional[IExecutionTracker] = None,
        orchestrator: Optional[IExecutionOrchestrator] = None,
    ) -> None:
        """Initializes ExecutionProvider with injected or default components."""
        self._lock = threading.RLock()
        self._coordinator = coordinator or ExecutionCoordinator()
        self._router = router or ExecutionRouter()
        self._tracker = tracker or ExecutionTracker()
        self._orchestrator = orchestrator or ExecutionOrchestrator(
            coordinator=self._coordinator,
            router=self._router,
            tracker=self._tracker,
        )

    def execute(
        self,
        request_or_prompt: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Execute a command request end-to-end.

        Args:
            request_or_prompt: ExecutionRequest, prompt string, or IntentResolution.
            context: Optional contextual parameters.

        Returns:
            Immutable ExecutionResult object.
        """
        with self._lock:
            return self._orchestrator.orchestrate(request_or_prompt, context=context)

    def health_check(self) -> ExecutionHealth:
        """Report overall component health statuses."""
        with self._lock:
            registered = {
                "ExecutionCoordinator": self._coordinator is not None,
                "ExecutionRouter": self._router is not None,
                "ExecutionTracker": self._tracker is not None,
                "ExecutionOrchestrator": self._orchestrator is not None,
            }
            all_ok = all(registered.values())

            return ExecutionHealth(
                status="READY" if all_ok else "ERROR",
                healthy=all_ok,
                components=registered,
                statistics=self.get_statistics().model_dump(),
                detected_issues=[] if all_ok else ["One or more orchestrator sub-components are unavailable"],
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> ExecutionStatistics:
        """Return diagnostic statistics snapshot."""
        with self._lock:
            return self._tracker.get_statistics()

    def clear(self) -> None:
        """Reset orchestrator execution statistics."""
        with self._lock:
            self._tracker.clear()
