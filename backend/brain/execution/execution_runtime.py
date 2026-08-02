"""Execution Runtime Manager for the Auralis Brain Execution Engine Subsystem (Phase 12.1).

Thread-safe singleton lifecycle manager orchestrating the ExecutionProvider.
Provides status transitions, process_request delegation, health monitoring, statistics reporting,
and 100% backward compatibility for legacy ExecutionPlan executions.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.execution.execution_coordinator import ExecutionCoordinator
from brain.execution.execution_models import (
    ExecutionHealth,
    ExecutionResult,
    ExecutionStatistics,
    ExecutionStatus,
)
from brain.execution.execution_policy import ExecutionPolicy
from brain.execution.execution_provider import ExecutionProvider
from brain.execution.execution_session import ExecutionSession
from brain.execution.execution_step_runner import ExecutionStepRunner
from brain.execution.interfaces import IExecutionRuntime
from brain.planning.execution_plan_builder import ExecutionPlan

logger = logging.getLogger(__name__)


class ExecutionRuntimeStatus(str, Enum):
    """Lifecycle status states for the Brain Execution Engine Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class ExecutionRuntime(IExecutionRuntime):
    """Thread-safe singleton runtime managing the ExecutionProvider lifecycle."""

    def __init__(
        self,
        provider: Optional[ExecutionProvider] = None,
        coordinator: Optional[ExecutionCoordinator] = None,
        step_runner: Optional[ExecutionStepRunner] = None,
        default_policy: Optional[ExecutionPolicy] = None,
    ) -> None:
        """Initializes the ExecutionRuntime with optional provider or legacy coordinator components."""
        self._lock = threading.RLock()
        self._status = ExecutionRuntimeStatus.INITIALIZING
        self._provider = provider or ExecutionProvider()

        # Legacy coordinator components
        self._step_runner = step_runner or ExecutionStepRunner()
        self._default_policy = default_policy or ExecutionPolicy()
        self._coordinator = coordinator or ExecutionCoordinator(
            step_runner=self._step_runner, default_policy=self._default_policy
        )

        self._active_sessions: Dict[str, ExecutionSession] = {}
        self._executions_started = 0
        self._executions_completed = 0
        self._executions_failed = 0
        self._total_runtime_ms = 0.0
        self._total_step_time_ms = 0.0
        self._total_steps_executed = 0
        self._peak_concurrent = 0
        self._cancellation_count = 0
        self._retry_count = 0
        self._rollback_count = 0

    @property
    def status(self) -> ExecutionRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> ExecutionProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Execution Engine runtime lifecycle.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == ExecutionRuntimeStatus.READY:
                return True

            try:
                self._status = ExecutionRuntimeStatus.READY
                logger.info("Brain Execution Engine Runtime Initialized")
                return True
            except Exception as exc:
                self._status = ExecutionRuntimeStatus.ERROR
                logger.error("ExecutionRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down active sessions and execution runtime.

        Returns:
            True always.
        """
        with self._lock:
            for session in list(self._active_sessions.values()):
                try:
                    session.cancel()
                except Exception:
                    pass
            self._active_sessions.clear()
            self._status = ExecutionRuntimeStatus.SHUTDOWN
            logger.info("Brain Execution Engine Runtime Shutdown")
            return True

    def process_request(self, request: Any) -> ExecutionResult:
        """Process an incoming request end-to-end through the ExecutionProvider.

        Args:
            request: ExecutionRequest, dict, BrainRequest, or prompt string.

        Returns:
            Immutable ExecutionResult object.
        """
        with self._lock:
            if self._status in (ExecutionRuntimeStatus.INITIALIZING, ExecutionRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = ExecutionRuntimeStatus.RUNNING

        try:
            return self._provider.execute(request)
        finally:
            with self._lock:
                if self._status == ExecutionRuntimeStatus.RUNNING:
                    self._status = prev_status if prev_status != ExecutionRuntimeStatus.INITIALIZING else ExecutionRuntimeStatus.READY

    # ------------------------------------------------------------------
    # Legacy ExecutionPlan Execution (Backward Compatibility)
    # ------------------------------------------------------------------

    def execute(
        self,
        plan: Optional[ExecutionPlan] = None,
        policy: Optional[ExecutionPolicy] = None,
    ) -> ExecutionResult:
        """Execute an ExecutionPlan via the internal ExecutionCoordinator."""
        with self._lock:
            if self._status == ExecutionRuntimeStatus.SHUTDOWN:
                self.initialize()

            effective_plan = plan if isinstance(plan, ExecutionPlan) else ExecutionPlan()
            effective_policy = policy or self._default_policy

            self._executions_started += 1
            curr_concurrent = len(self._active_sessions) + 1
            if curr_concurrent > self._peak_concurrent:
                self._peak_concurrent = curr_concurrent

            prev_status = self._status
            self._status = ExecutionRuntimeStatus.RUNNING

        try:
            result = self._coordinator.execute_plan(effective_plan, policy=effective_policy)
        finally:
            with self._lock:
                self._status = prev_status if prev_status != ExecutionRuntimeStatus.INITIALIZING else ExecutionRuntimeStatus.READY

                if result.status == ExecutionStatus.COMPLETED:
                    self._executions_completed += 1
                elif result.status in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED):
                    self._executions_failed += 1
                elif result.status == ExecutionStatus.CANCELLED:
                    self._cancellation_count += 1

                self._total_runtime_ms += result.execution_time
                for sr in result.step_results:
                    self._total_steps_executed += 1
                    self._total_step_time_ms += sr.duration_ms
                    if sr.status == ExecutionStatus.ROLLING_BACK:
                        self._rollback_count += 1
                    if sr.metadata and sr.metadata.get("attempt", 1) > 1:
                        self._retry_count += (sr.metadata["attempt"] - 1)

        return result

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution session."""
        with self._lock:
            session = self._active_sessions.get(execution_id)
            if session:
                canceled = session.cancel()
                if canceled:
                    self._cancellation_count += 1
                return canceled
            return False

    def pause_execution(self, execution_id: str) -> bool:
        """Pause an active execution session."""
        with self._lock:
            session = self._active_sessions.get(execution_id)
            return session.pause() if session else False

    def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution session."""
        with self._lock:
            session = self._active_sessions.get(execution_id)
            return session.resume() if session else False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List active execution sessions."""
        with self._lock:
            return [
                {
                    "execution_id": sid,
                    "status": s.status.value,
                    "progress": s.context.progress_percentage,
                }
                for sid, s in self._active_sessions.items()
            ]

    def list_components(self) -> List[str]:
        """List registered execution components."""
        return [
            "ExecutionStepRunner",
            "ExecutionCoordinator",
            "ExecutionPolicy",
        ]

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def health_check(self) -> ExecutionHealth:
        """Fetch health check status report."""
        with self._lock:
            registered = {
                "ExecutionStepRunner": self._step_runner is not None,
                "ExecutionCoordinator": self._coordinator is not None,
                "ExecutionPolicy": self._default_policy is not None,
            }
            all_ok = all(registered.values())
            is_healthy = (self._status in (ExecutionRuntimeStatus.READY, ExecutionRuntimeStatus.RUNNING)) and all_ok

            issues = []
            if not all_ok:
                issues.append("One or more execution components are unavailable")
            if self._status == ExecutionRuntimeStatus.ERROR:
                issues.append("Execution runtime is in ERROR status")

            return ExecutionHealth(
                status=self._status,
                healthy=is_healthy,
                components=registered,
                registered_components=registered,
                statistics=self.get_statistics().model_dump(),
                current_sessions=len(self._active_sessions),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> ExecutionStatistics:
        """Fetch runtime statistics snapshot."""
        with self._lock:
            prov_stats = self._provider.get_statistics()

            started = self._executions_started or prov_stats.total_requests
            completed = self._executions_completed or prov_stats.successful_executions
            failed = self._executions_failed or prov_stats.failed_executions
            cancelled = self._cancellation_count or prov_stats.cancelled_executions

            avg_rt = (self._total_runtime_ms / started) if started > 0 else prov_stats.average_execution_time_ms
            avg_st = (self._total_step_time_ms / self._total_steps_executed) if self._total_steps_executed > 0 else 0.0

            return ExecutionStatistics(
                total_requests=started,
                successful_executions=completed,
                failed_executions=failed,
                cancelled_executions=cancelled,
                average_execution_time_ms=avg_rt,
                decisions_by_type=prov_stats.decisions_by_type,
                active_sessions=prov_stats.active_sessions + len(self._active_sessions),
                executions_started=started,
                executions_completed=completed,
                executions_failed=failed,
                average_runtime_ms=avg_rt,
                average_step_time_ms=avg_st,
                current_running_sessions=len(self._active_sessions),
                peak_concurrent_sessions=self._peak_concurrent,
                cancellation_count=cancelled,
                retry_count=self._retry_count,
                rollback_count=self._rollback_count,
                metadata={
                    "executions_started": started,
                    "executions_completed": completed,
                    "executions_failed": failed,
                    "average_runtime_ms": avg_rt,
                    "average_step_time_ms": avg_st,
                    "current_running_sessions": len(self._active_sessions),
                    "peak_concurrent_sessions": self._peak_concurrent,
                    "cancellation_count": cancelled,
                    "retry_count": self._retry_count,
                    "rollback_count": self._rollback_count,
                },
            )

    def clear(self) -> None:
        """Reset execution statistics and active session registry."""
        with self._lock:
            self._provider.clear()
            self._active_sessions.clear()
            self._executions_started = 0
            self._executions_completed = 0
            self._executions_failed = 0
            self._total_runtime_ms = 0.0
            self._total_step_time_ms = 0.0
            self._total_steps_executed = 0
            self._peak_concurrent = 0
            self._cancellation_count = 0
            self._retry_count = 0
            self._rollback_count = 0
            if self._status != ExecutionRuntimeStatus.SHUTDOWN:
                self._status = ExecutionRuntimeStatus.READY
            logger.info("ExecutionRuntime cleared")
