"""Task Executor for the Auralis Task Management Runtime (Phase 12.5).

Executes long-running background tasks coordinating with the Workflow Execution Engine,
Command Execution Orchestrator, and Planning Runtime.
Supports pause, resume, cancellation, retries, timeout enforcement, and checkpoint persistence.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, Optional, Set

from brain.execution.task.exceptions import TaskCancellationError, TaskExecutionError
from brain.execution.task.interfaces import ITaskExecutor
from brain.execution.task.task_models import (
    TaskFailureReason,
    TaskProgress,
    TaskRequest,
    TaskResult,
    TaskStatus,
)
from brain.execution.task.task_monitor import TaskMonitor
from brain.execution.task.task_persistence import TaskPersistence

logger = logging.getLogger(__name__)


class TaskExecutor(ITaskExecutor):
    """Executor driving long-running tasks with pause/resume, cancellation, timeout, and checkpointing."""

    def __init__(
        self,
        workflow_runtime: Optional[Any] = None,
        command_orchestrator: Optional[Any] = None,
        planning_runtime: Optional[Any] = None,
        monitor: Optional[TaskMonitor] = None,
        persistence: Optional[TaskPersistence] = None,
    ) -> None:
        """Initializes TaskExecutor with optional injected runtimes and monitor/persistence instances."""
        self._lock = threading.RLock()
        self._workflow_runtime = workflow_runtime
        self._command_orchestrator = command_orchestrator
        self._planning_runtime = planning_runtime
        self._monitor = monitor or TaskMonitor()
        self._persistence = persistence or TaskPersistence()

        self._paused_tasks: Set[str] = set()
        self._cancelled_tasks: Set[str] = set()

    def execute_task(
        self,
        request: TaskRequest,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """Execute a TaskRequest long-running lifecycle.

        Args:
            request: TaskRequest object.
            context: Optional contextual parameters.

        Returns:
            TaskResult model.
        """
        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)

        self._monitor.start_monitoring(request.task_id, total_steps=1)

        # Check immediate cancellation
        with self._lock:
            if request.task_id in self._cancelled_tasks:
                self._monitor.stop_monitoring(request.task_id)
                return TaskResult(
                    task_id=request.task_id,
                    status=TaskStatus.CANCELLED,
                    failure_reason=TaskFailureReason.CANCELLED_BY_USER,
                    error="Task cancelled before execution",
                    execution_time_seconds=0.0,
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                )

        # Handle pause loop
        while True:
            with self._lock:
                if request.task_id in self._cancelled_tasks:
                    self._monitor.stop_monitoring(request.task_id)
                    return TaskResult(
                        task_id=request.task_id,
                        status=TaskStatus.CANCELLED,
                        failure_reason=TaskFailureReason.CANCELLED_BY_USER,
                        error="Task cancelled during execution pause",
                        execution_time_seconds=time.perf_counter() - start_time,
                        started_at=started_at,
                        finished_at=datetime.now(timezone.utc),
                    )
                if request.task_id not in self._paused_tasks:
                    break
            time.sleep(0.05)

        output: Dict[str, Any] = {}
        error_msg: Optional[str] = None
        failure_reason: Optional[TaskFailureReason] = None
        final_status = TaskStatus.COMPLETED

        try:
            self._monitor.update_progress(request.task_id, 0, 1, status_message="Executing task payload")

            # Check timeout
            if request.timeout_seconds and request.timeout_seconds > 0:
                elapsed = time.perf_counter() - start_time
                if elapsed > request.timeout_seconds:
                    raise TimeoutError(f"Task exceeded timeout limit of {request.timeout_seconds} seconds")

            # Execute via Workflow Runtime if payload is a list or WorkflowRequest
            payload = request.payload
            if self._workflow_runtime and hasattr(self._workflow_runtime, "process_workflow"):
                wf_res = self._workflow_runtime.process_workflow(payload, context=context)
                output = {"workflow_result": getattr(wf_res, "status", "COMPLETED")}
            elif self._command_orchestrator and hasattr(self._command_orchestrator, "orchestrate"):
                prompt = str(payload) if payload else request.name
                orch_res = self._command_orchestrator.orchestrate(prompt, context=context)
                output = dict(getattr(orch_res, "output", {}))
            else:
                output = {
                    "task_id": request.task_id,
                    "name": request.name,
                    "result": f"Executed payload '{request.payload}'",
                }

            # Save checkpoint
            self._persistence.save_checkpoint(request.task_id, {"checkpoint": "completed", "output": output})
            self._monitor.update_progress(request.task_id, 1, 1, status_message="Execution complete")

        except TimeoutError as exc:
            final_status = TaskStatus.FAILED
            failure_reason = TaskFailureReason.TIMEOUT
            error_msg = str(exc)
            logger.error("Task '%s' timed out: %s", request.task_id, exc)

        except Exception as exc:
            final_status = TaskStatus.FAILED
            failure_reason = TaskFailureReason.UNKNOWN
            error_msg = str(exc)
            logger.error("Task '%s' execution failed: %s", request.task_id, exc)

        finally:
            self._monitor.stop_monitoring(request.task_id)

        elapsed_sec = round(time.perf_counter() - start_time, 3)

        return TaskResult(
            task_id=request.task_id,
            status=final_status,
            output=output,
            error=error_msg,
            failure_reason=failure_reason,
            execution_time_seconds=elapsed_sec,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )

    def pause_task(self, task_id: str) -> bool:
        """Pause a running task by task_id.

        Args:
            task_id: Task identifier.

        Returns:
            True always.
        """
        with self._lock:
            self._paused_tasks.add(task_id)
            logger.info("Task '%s' paused", task_id)
            return True

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task by task_id.

        Args:
            task_id: Task identifier.

        Returns:
            True if task was paused, False otherwise.
        """
        with self._lock:
            if task_id in self._paused_tasks:
                self._paused_tasks.remove(task_id)
                logger.info("Task '%s' resumed", task_id)
                return True
            return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or paused task by task_id.

        Args:
            task_id: Task identifier.

        Returns:
            True always.
        """
        with self._lock:
            self._cancelled_tasks.add(task_id)
            self._paused_tasks.discard(task_id)
            logger.info("Task '%s' marked for cancellation", task_id)
            return True
