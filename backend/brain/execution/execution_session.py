"""Execution Session for managing plan execution lifecycle and state aggregation.

This module provides thread-safe session management, tracking status transitions,
step execution results, timing metrics, and generating final immutable ExecutionResult snapshots.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.execution.execution_context import ExecutionContext
from brain.execution.execution_models import ExecutionResult, ExecutionStatus, ExecutionStepResult

logger = logging.getLogger(__name__)


class ExecutionSession:
    """Thread-safe manager for an active plan execution session."""

    def __init__(self, context: ExecutionContext) -> None:
        """Initializes the ExecutionSession with an ExecutionContext."""
        self._lock = threading.RLock()
        self._context = context
        self._execution_id = context.execution_id
        self._status = ExecutionStatus.PENDING

        self._started_at: Optional[datetime] = None
        self._finished_at: Optional[datetime] = None
        self._start_perf_time: Optional[float] = None

        self._step_results: List[ExecutionStepResult] = []
        self._completed_steps = 0
        self._failed_steps = 0
        self._cancelled_steps = 0

    @property
    def execution_id(self) -> str:
        return self._execution_id

    @property
    def context(self) -> ExecutionContext:
        return self._context

    @property
    def status(self) -> ExecutionStatus:
        with self._lock:
            return self._status

    def start(self) -> bool:
        """Transitions session status to RUNNING and records start timestamp."""
        with self._lock:
            if self._status in (ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED):
                return False

            self._status = ExecutionStatus.RUNNING
            self._started_at = datetime.now(timezone.utc)
            self._start_perf_time = time.perf_counter()
            logger.info("Execution Started: execution_id=%s", self._execution_id)
            return True

    def pause(self) -> bool:
        """Transitions session status to PAUSED if currently running."""
        with self._lock:
            if self._status == ExecutionStatus.RUNNING:
                self._status = ExecutionStatus.PAUSED
                self._context.request_pause()
                logger.info("Execution Paused: execution_id=%s", self._execution_id)
                return True
            return False

    def resume(self) -> bool:
        """Transitions session status back to RUNNING if paused."""
        with self._lock:
            if self._status == ExecutionStatus.PAUSED:
                self._status = ExecutionStatus.RUNNING
                self._context.resume()
                logger.info("Execution Resumed: execution_id=%s", self._execution_id)
                return True
            return False

    def cancel(self) -> bool:
        """Transitions session status to CANCELLED and marks cancellation token."""
        with self._lock:
            if self._status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
                return False

            self._status = ExecutionStatus.CANCELLED
            self._context.request_cancellation()
            self._finished_at = datetime.now(timezone.utc)
            logger.info("Execution Cancelled: execution_id=%s", self._execution_id)
            return True

    def record_step_result(self, step_result: ExecutionStepResult) -> None:
        """Records a completed or failed step execution result."""
        with self._lock:
            self._step_results.append(step_result)

            if step_result.status == ExecutionStatus.COMPLETED:
                self._completed_steps += 1
                self._context.increment_completed_steps()
            elif step_result.status == ExecutionStatus.FAILED:
                self._failed_steps += 1
            elif step_result.status == ExecutionStatus.CANCELLED:
                self._cancelled_steps += 1

    def complete(self, final_status: Optional[ExecutionStatus] = None) -> ExecutionResult:
        """Finalizes the session lifecycle and returns an immutable ExecutionResult."""
        with self._lock:
            now = datetime.now(timezone.utc)
            self._finished_at = now

            if final_status:
                self._status = final_status
            elif self._context.cancellation_requested:
                self._status = ExecutionStatus.CANCELLED
            elif self._failed_steps > 0 and not self._context.policy.continue_on_error:
                self._status = ExecutionStatus.FAILED
            else:
                self._status = ExecutionStatus.COMPLETED

            duration = 0.0
            if self._start_perf_time is not None:
                duration = (time.perf_counter() - self._start_perf_time) * 1000.0

            result = ExecutionResult(
                execution_id=self._execution_id,
                status=self._status,
                step_results=list(self._step_results),
                completed_steps=self._completed_steps,
                failed_steps=self._failed_steps,
                cancelled_steps=self._cancelled_steps,
                execution_time=duration,
                started_at=self._started_at,
                finished_at=self._finished_at,
                metadata=self._context.metadata,
            )

            if self._status == ExecutionStatus.COMPLETED:
                logger.info("Execution Completed: execution_id=%s", self._execution_id)
            elif self._status == ExecutionStatus.FAILED:
                logger.info("Execution Failed: execution_id=%s", self._execution_id)

            return result
