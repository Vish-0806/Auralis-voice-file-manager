"""Execution Runtime Coordinator for managing the complete Execution Engine subsystem.

This module provides thread-safe runtime orchestration, session tracking, health monitoring,
statistics aggregation, pause/resume/cancellation controls, and singleton lifecycle management.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.execution.execution_coordinator import ExecutionCoordinator
from brain.execution.execution_models import ExecutionResult, ExecutionStatus
from brain.execution.execution_policy import ExecutionPolicy
from brain.execution.execution_session import ExecutionSession
from brain.execution.execution_step_runner import ExecutionStepRunner
from brain.planning.execution_plan_builder import ExecutionPlan

logger = logging.getLogger(__name__)


class ExecutionRuntimeStatus(str, Enum):
    """Enumeration representing execution runtime lifecycle status states."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class ExecutionRuntimeStatistics(BaseModel):
    """Immutable model representing diagnostic statistics of the Execution Engine."""

    model_config = ConfigDict(frozen=True)

    executions_started: int = 0
    executions_completed: int = 0
    executions_failed: int = 0
    average_runtime_ms: float = 0.0
    average_step_time_ms: float = 0.0
    current_running_sessions: int = 0
    peak_concurrent_sessions: int = 0
    cancellation_count: int = 0
    retry_count: int = 0
    rollback_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionRuntimeHealth(BaseModel):
    """Immutable model representing health status of the Execution Engine."""

    model_config = ConfigDict(frozen=True)

    status: ExecutionRuntimeStatus = ExecutionRuntimeStatus.READY
    healthy: bool = True
    registered_components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    current_sessions: int = 0
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionRuntimeCoordinator:
    """Singleton runtime coordinator orchestrating the Execution Engine."""

    def __init__(
        self,
        coordinator: Optional[ExecutionCoordinator] = None,
        step_runner: Optional[ExecutionStepRunner] = None,
        default_policy: Optional[ExecutionPolicy] = None,
    ) -> None:
        """Initializes the ExecutionRuntimeCoordinator."""
        self._lock = threading.RLock()
        self._status = ExecutionRuntimeStatus.INITIALIZING

        self._step_runner = step_runner or ExecutionStepRunner()
        self._default_policy = default_policy or ExecutionPolicy()
        self._coordinator = coordinator or ExecutionCoordinator(step_runner=self._step_runner, default_policy=self._default_policy)

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

    def initialize(self) -> bool:
        """Initializes execution runtime components and sets status to READY."""
        with self._lock:
            if self._status == ExecutionRuntimeStatus.READY:
                return True

            self._status = ExecutionRuntimeStatus.READY
            logger.info("Runtime Initialized")
            return True

    def shutdown(self) -> bool:
        """Shuts down active sessions and transitions status to SHUTDOWN."""
        with self._lock:
            if self._status == ExecutionRuntimeStatus.SHUTDOWN:
                return True

            for session in list(self._active_sessions.values()):
                session.cancel()

            self._active_sessions.clear()
            self._status = ExecutionRuntimeStatus.SHUTDOWN
            logger.info("Runtime Shutdown")
            return True

    def clear(self) -> None:
        """Resets execution statistics and active session registry."""
        with self._lock:
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

    def execute(
        self,
        plan: Optional[ExecutionPlan] = None,
        policy: Optional[ExecutionPolicy] = None,
    ) -> ExecutionResult:
        """Executes an ExecutionPlan deterministically."""
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
                elif result.status == ExecutionStatus.FAILED:
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
        """Requests cancellation of an active execution session."""
        with self._lock:
            session = self._active_sessions.get(execution_id)
            if session:
                canceled = session.cancel()
                if canceled:
                    self._cancellation_count += 1
                return canceled
            return False

    def pause_execution(self, execution_id: str) -> bool:
        """Requests pausing of an active execution session."""
        with self._lock:
            session = self._active_sessions.get(execution_id)
            if session:
                return session.pause()
            return False

    def resume_execution(self, execution_id: str) -> bool:
        """Requests resuming of a paused execution session."""
        with self._lock:
            session = self._active_sessions.get(execution_id)
            if session:
                return session.resume()
            return False

    def health_check(self) -> ExecutionRuntimeHealth:
        """Generates a real-time Execution Engine health status report."""
        with self._lock:
            components = {
                "ExecutionStepRunner": self._step_runner is not None,
                "ExecutionCoordinator": self._coordinator is not None,
                "ExecutionPolicy": self._default_policy is not None,
            }
            all_ok = all(components.values())
            is_healthy = (self._status in (ExecutionRuntimeStatus.READY, ExecutionRuntimeStatus.RUNNING)) and all_ok

            issues = []
            if not all_ok:
                issues.append("One or more execution components are unavailable")
            if self._status == ExecutionRuntimeStatus.ERROR:
                issues.append("Execution runtime is in ERROR status")

            return ExecutionRuntimeHealth(
                status=self._status,
                healthy=is_healthy,
                registered_components=components,
                statistics=self.get_statistics().model_dump(),
                current_sessions=len(self._active_sessions),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> ExecutionRuntimeStatistics:
        """Retrieves runtime statistics snapshot."""
        with self._lock:
            avg_rt = (self._total_runtime_ms / self._executions_started) if self._executions_started > 0 else 0.0
            avg_st = (self._total_step_time_ms / self._total_steps_executed) if self._total_steps_executed > 0 else 0.0

            return ExecutionRuntimeStatistics(
                executions_started=self._executions_started,
                executions_completed=self._executions_completed,
                executions_failed=self._executions_failed,
                average_runtime_ms=avg_rt,
                average_step_time_ms=avg_st,
                current_running_sessions=len(self._active_sessions),
                peak_concurrent_sessions=self._peak_concurrent,
                cancellation_count=self._cancellation_count,
                retry_count=self._retry_count,
                rollback_count=self._rollback_count,
                metadata={},
            )

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Lists active execution sessions."""
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
        """Lists registered execution components."""
        return [
            "ExecutionStepRunner",
            "ExecutionCoordinator",
            "ExecutionPolicy",
        ]


_global_execution_lock = threading.RLock()
_global_execution_runtime: Optional[ExecutionRuntimeCoordinator] = None


def get_execution_runtime(
    coordinator: Optional[ExecutionCoordinator] = None,
    step_runner: Optional[ExecutionStepRunner] = None,
    default_policy: Optional[ExecutionPolicy] = None,
    reset: bool = False,
) -> ExecutionRuntimeCoordinator:
    """Singleton accessor for the global ExecutionRuntimeCoordinator instance."""
    global _global_execution_runtime
    with _global_execution_lock:
        if reset or _global_execution_runtime is None:
            _global_execution_runtime = ExecutionRuntimeCoordinator(
                coordinator=coordinator,
                step_runner=step_runner,
                default_policy=default_policy,
            )
            _global_execution_runtime.initialize()
        return _global_execution_runtime


def reset_execution_runtime() -> None:
    """Resets the global ExecutionRuntimeCoordinator instance."""
    global _global_execution_runtime
    with _global_execution_lock:
        if _global_execution_runtime is not None:
            _global_execution_runtime.shutdown()
            _global_execution_runtime.clear()
            _global_execution_runtime = None
