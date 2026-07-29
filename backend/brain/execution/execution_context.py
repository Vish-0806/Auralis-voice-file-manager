"""Execution Context for tracking transient state during execution plan processing.

This module provides thread-safe encapsulation of the ExecutionPlan, current step pointer,
progress calculation, cancellation tokens, pause tokens, retry counters, timeouts,
and backward compatibility for legacy ExecutionContext callers.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, Optional
import uuid

from brain.execution.execution_policy import ExecutionPolicy
from brain.planning.execution_plan_builder import ExecutionPlan

logger = logging.getLogger(__name__)


class ExecutionContext:
    """Thread-safe context tracking transient state during plan execution."""

    def __init__(
        self,
        plan: Optional[Any] = None,
        policy: Optional[ExecutionPolicy] = None,
        execution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initializes ExecutionContext supporting both Phase 9.4 and legacy callers."""
        self._lock = threading.RLock()
        self._logger = logger or logging.getLogger(__name__)

        # Backward compatibility for legacy positional usage: ExecutionContext("exec_1")
        if isinstance(plan, str) and execution_id is None:
            execution_id = plan
            plan = None

        self._plan = plan if isinstance(plan, ExecutionPlan) else ExecutionPlan()
        self._policy = policy or ExecutionPolicy()
        self._execution_id = execution_id or f"exec-{uuid.uuid4().hex[:8]}"

        self._current_step_number: Optional[int] = None
        self._completed_steps_count = 0
        self._total_steps_count = len(self._plan.execution_order) if self._plan.execution_order else len(self._plan.action_plan.steps)

        self._cancellation_requested = False
        self._pause_requested = False
        self._retry_counter: Dict[int, int] = {}

        self._created_at = datetime.now(timezone.utc)
        self._metadata = dict(metadata or {})
        if self._plan.metadata:
            for k, v in self._plan.metadata.items():
                if k not in self._metadata:
                    self._metadata[k] = v

        self._legacy_model = None

    @property
    def plan(self) -> ExecutionPlan:
        return self._plan

    @property
    def policy(self) -> ExecutionPolicy:
        return self._policy

    @property
    def execution_id(self) -> str:
        return self._execution_id

    @property
    def model(self) -> Any:
        """Legacy model accessor for pre-existing execution engine components."""
        with self._lock:
            if self._legacy_model is None:
                from .models import ExecutionContext as ContextModel
                self._legacy_model = ContextModel(
                    execution_id=self._execution_id,
                    completed_steps=[],
                )
            return self._legacy_model

    def start_step(self, step_id: str, capability: str) -> None:
        """Legacy helper for step start event tracking."""
        with self._lock:
            m = self.model
            m.current_step = step_id
            m.current_capability = capability
            self._logger.debug(
                "Execution step started",
                extra={"execution_id": self._execution_id, "step_id": step_id, "capability": capability},
            )

    def complete_step(self, step_id: str, result: Dict[str, Any]) -> None:
        """Legacy helper for step completion tracking."""
        with self._lock:
            m = self.model
            if step_id == m.current_step:
                m.current_step = None
                m.current_capability = None
            m.completed_steps.append(step_id)
            m.last_execution_result = result
            self._completed_steps_count = len(m.completed_steps)
            self._logger.debug(
                "Execution step completed",
                extra={"execution_id": self._execution_id, "step_id": step_id},
            )

    @property
    def current_step_number(self) -> Optional[int]:
        with self._lock:
            return self._current_step_number

    @current_step_number.setter
    def current_step_number(self, step_num: Optional[int]) -> None:
        with self._lock:
            self._current_step_number = step_num

    @property
    def progress_percentage(self) -> float:
        with self._lock:
            if self._total_steps_count == 0:
                return 100.0
            return (self._completed_steps_count / self._total_steps_count) * 100.0

    @property
    def completed_steps_count(self) -> int:
        with self._lock:
            return self._completed_steps_count

    def increment_completed_steps(self) -> int:
        with self._lock:
            self._completed_steps_count += 1
            return self._completed_steps_count

    @property
    def cancellation_requested(self) -> bool:
        with self._lock:
            return self._cancellation_requested

    def request_cancellation(self) -> bool:
        with self._lock:
            if not self._cancellation_requested:
                self._cancellation_requested = True
                logger.info("Cancellation Requested: execution_id=%s", self._execution_id)
                return True
            return False

    @property
    def pause_requested(self) -> bool:
        with self._lock:
            return self._pause_requested

    def request_pause(self) -> bool:
        with self._lock:
            if not self._pause_requested:
                self._pause_requested = True
                logger.info("Pause Requested: execution_id=%s", self._execution_id)
                return True
            return False

    def resume(self) -> bool:
        with self._lock:
            if self._pause_requested:
                self._pause_requested = False
                logger.info("Resume Triggered: execution_id=%s", self._execution_id)
                return True
            return False

    def get_retry_count(self, step_number: int) -> int:
        with self._lock:
            return self._retry_counter.get(step_number, 0)

    def increment_retry(self, step_number: int) -> int:
        with self._lock:
            count = self._retry_counter.get(step_number, 0) + 1
            self._retry_counter[step_number] = count
            return count

    @property
    def metadata(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._metadata)
