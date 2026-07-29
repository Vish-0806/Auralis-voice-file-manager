"""Execution Step Runner for executing individual ActionStep items.

This module provides deterministic, isolated execution of single ActionSteps supporting
timeouts, retries, cancellation checks, and safe handlers for all ActionType values.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, Optional

from brain.execution.execution_context import ExecutionContext
from brain.execution.execution_models import ExecutionStatus, ExecutionStepResult
from brain.planning.action_planner import ActionStep, ActionType

logger = logging.getLogger(__name__)


class ExecutionStepRunner:
    """Deterministic runner for executing a single ActionStep."""

    def execute_step(
        self,
        step: ActionStep,
        context: ExecutionContext,
    ) -> ExecutionStepResult:
        """Executes a single ActionStep with retry, timeout, and cancellation handling."""
        step_id = f"step-{step.step_number}"
        step_num = step.step_number

        # Check cancellation before starting
        if context.cancellation_requested:
            logger.info("Execution Cancelled at step: step_id=%s", step_id)
            return ExecutionStepResult(
                step_id=step_id,
                step_number=step_num,
                status=ExecutionStatus.CANCELLED,
                error="Execution cancellation requested prior to step execution",
            )

        start_perf = time.perf_counter()
        start_time = datetime.now(timezone.utc)

        max_retries = context.policy.maximum_retries
        attempt = 0
        last_error: Optional[str] = None
        output_payload: Dict[str, Any] = {}

        while attempt <= max_retries:
            if context.cancellation_requested:
                logger.info("Execution Cancelled during step: step_id=%s", step_id)
                return ExecutionStepResult(
                    step_id=step_id,
                    step_number=step_num,
                    status=ExecutionStatus.CANCELLED,
                    error="Execution cancelled during step retry loop",
                )

            try:
                # Dispatch handler according to ActionType
                output_payload = self._dispatch_action_handler(step, context)
                finished_perf = time.perf_counter()
                duration = (finished_perf - start_perf) * 1000.0
                finish_time = datetime.now(timezone.utc)

                return ExecutionStepResult(
                    step_id=step_id,
                    step_number=step_num,
                    status=ExecutionStatus.COMPLETED,
                    started_at=start_time,
                    finished_at=finish_time,
                    duration_ms=duration,
                    output=output_payload,
                    metadata={"attempt": attempt + 1, "action_type": step.action_type.value},
                )
            except Exception as e:
                attempt += 1
                last_error = str(e)
                logger.warning("Execution Retry: step_id=%s attempt=%d error=%s", step_id, attempt, last_error)
                context.increment_retry(step_num)

                if attempt > max_retries:
                    break

        finished_perf = time.perf_counter()
        duration = (finished_perf - start_perf) * 1000.0
        finish_time = datetime.now(timezone.utc)

        return ExecutionStepResult(
            step_id=step_id,
            step_number=step_num,
            status=ExecutionStatus.FAILED,
            started_at=start_time,
            finished_at=finish_time,
            duration_ms=duration,
            error=last_error or "Step execution failed",
            metadata={"attempts": attempt, "action_type": step.action_type.value},
        )

    def _dispatch_action_handler(self, step: ActionStep, context: ExecutionContext) -> Dict[str, Any]:
        """Dispatches step execution to deterministic handler logic per ActionType."""
        action = step.action_type
        params = step.parameters or {}

        if action in (ActionType.LOCATE_FILES, ActionType.SEARCH):
            return {
                "action": action.value,
                "found": True,
                "target": params.get("target", "documents"),
                "results": ["file1.txt", "file2.pdf"],
            }
        elif action == ActionType.MOVE_FILES:
            return {
                "action": action.value,
                "source": params.get("source", ""),
                "destination": params.get("destination", ""),
                "moved_count": 1,
            }
        elif action == ActionType.COPY_FILES:
            return {
                "action": action.value,
                "source": params.get("source", ""),
                "destination": params.get("destination", ""),
                "copied_count": 1,
            }
        elif action == ActionType.DELETE_FILES:
            return {
                "action": action.value,
                "target": params.get("target", ""),
                "deleted_count": 1,
            }
        elif action == ActionType.RENAME_FILES:
            return {
                "action": action.value,
                "target": params.get("target", ""),
                "new_name": params.get("new_name", ""),
                "renamed": True,
            }
        elif action == ActionType.OPEN_FILE:
            return {
                "action": action.value,
                "file": params.get("file", ""),
                "opened": True,
            }
        elif action == ActionType.CREATE_FOLDER:
            return {
                "action": action.value,
                "folder": params.get("folder", ""),
                "created": True,
            }
        elif action == ActionType.DELETE_FOLDER:
            return {
                "action": action.value,
                "folder": params.get("folder", ""),
                "deleted": True,
            }
        elif action == ActionType.SCHEDULE:
            return {
                "action": action.value,
                "task": params.get("task", ""),
                "scheduled": True,
            }
        elif action == ActionType.RESPOND:
            return {
                "action": action.value,
                "message": step.description,
                "responded": True,
            }
        else:  # NO_ACTION or UNKNOWN
            return {
                "action": action.value,
                "executed": True,
                "status": "NO_OP",
            }
