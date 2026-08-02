"""Workflow Provider for the Auralis Workflow Execution Engine (Phase 12.4).

Aggregates Builder, Validator, Scheduler, and Executor into a unified, thread-safe provider.
Supports end-to-end workflow graph building, validation, topological scheduling, execution, health monitoring, and statistics.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.execution.workflow.exceptions import WorkflowValidationError
from brain.execution.workflow.interfaces import (
    IWorkflowBuilder,
    IWorkflowExecutor,
    IWorkflowProvider,
    IWorkflowScheduler,
    IWorkflowValidator,
)
from brain.execution.workflow.workflow_builder import WorkflowBuilder
from brain.execution.workflow.workflow_executor import WorkflowExecutor
from brain.execution.workflow.workflow_models import (
    WorkflowHealth,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatistics,
    WorkflowStatus,
    WorkflowStep,
)
from brain.execution.workflow.workflow_scheduler import WorkflowScheduler
from brain.execution.workflow.workflow_validator import WorkflowValidator

logger = logging.getLogger(__name__)


class WorkflowProvider(IWorkflowProvider):
    """Thread-safe provider aggregating workflow builder, validator, scheduler, and executor."""

    def __init__(
        self,
        builder: Optional[IWorkflowBuilder] = None,
        validator: Optional[IWorkflowValidator] = None,
        scheduler: Optional[IWorkflowScheduler] = None,
        executor: Optional[IWorkflowExecutor] = None,
    ) -> None:
        """Initializes WorkflowProvider with injected or default components."""
        self._lock = threading.RLock()
        self._builder = builder or WorkflowBuilder()
        self._validator = validator or WorkflowValidator()
        self._scheduler = scheduler or WorkflowScheduler()
        self._executor = executor or WorkflowExecutor()

        self._total_workflows = 0
        self._completed_count = 0
        self._failed_count = 0
        self._cancelled_count = 0
        self._total_execution_time_ms = 0.0
        self._total_steps_executed = 0

    def execute_workflow(
        self,
        request_or_steps: Any,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[Dict[str, bool]] = None,
    ) -> WorkflowResult:
        """Process workflow request end-to-end through building, validation, scheduling, and execution.

        Args:
            request_or_steps: WorkflowRequest, List[WorkflowStep], or dict payload.
            context: Optional contextual parameters.
            cancellation_token: Optional cancellation token dict.

        Returns:
            WorkflowResult model.

        Raises:
            WorkflowValidationError: If workflow validation fails due to graph defects.
        """
        start_time = time.perf_counter()
        with self._lock:
            self._total_workflows += 1

        try:
            if isinstance(request_or_steps, WorkflowRequest):
                wf_request = request_or_steps
            elif isinstance(request_or_steps, list):
                wf_request = self._builder.build_workflow(
                    name="Dynamic Workflow",
                    steps=request_or_steps,
                    context=context,
                )
            elif isinstance(request_or_steps, dict):
                steps_data = request_or_steps.get("steps", [])
                steps_objs = [s if isinstance(s, WorkflowStep) else WorkflowStep(**s) for s in steps_data]
                wf_request = self._builder.build_workflow(
                    name=request_or_steps.get("name", "Dynamic Workflow"),
                    steps=steps_objs,
                    context=context or request_or_steps.get("context", {}),
                )
            else:
                raise WorkflowValidationError(f"Invalid workflow input type: {type(request_or_steps)}")

            # Validate graph
            diagnostics = self._validator.validate_workflow(wf_request)
            if diagnostics:
                raise WorkflowValidationError(f"Workflow validation failed: {'; '.join(diagnostics)}")

            # Schedule graph
            execution_schedule = self._scheduler.schedule(wf_request)

            # Execute graph
            result = self._executor.execute(
                execution=execution_schedule,
                request=wf_request,
                cancellation_token=cancellation_token,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            with self._lock:
                if result.status == WorkflowStatus.COMPLETED:
                    self._completed_count += 1
                elif result.status == WorkflowStatus.CANCELLED:
                    self._cancelled_count += 1
                else:
                    self._failed_count += 1

                self._total_execution_time_ms += elapsed_ms
                self._total_steps_executed += result.completed_steps

            return result

        except Exception as exc:
            logger.error("Workflow execution failed: %s", exc)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            with self._lock:
                self._failed_count += 1

            return WorkflowResult(
                workflow_id=getattr(request_or_steps, "request_id", "wf-unknown"),
                status=WorkflowStatus.FAILED,
                execution_time_ms=elapsed_ms,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                metadata={"error": str(exc)},
            )

    def health_check(self) -> WorkflowHealth:
        """Report component health statuses."""
        with self._lock:
            registered = {
                "WorkflowBuilder": self._builder is not None,
                "WorkflowValidator": self._validator is not None,
                "WorkflowScheduler": self._scheduler is not None,
                "WorkflowExecutor": self._executor is not None,
            }
            all_ok = all(registered.values())

            return WorkflowHealth(
                status="READY" if all_ok else "ERROR",
                healthy=all_ok,
                components=registered,
                statistics=self.get_statistics().model_dump(),
                detected_issues=[] if all_ok else ["One or more workflow sub-components are unavailable"],
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> WorkflowStatistics:
        """Return snapshot of aggregated workflow execution statistics."""
        with self._lock:
            avg_time = (self._total_execution_time_ms / self._total_workflows) if self._total_workflows > 0 else 0.0
            return WorkflowStatistics(
                total_workflows=self._total_workflows,
                completed_count=self._completed_count,
                failed_count=self._failed_count,
                cancelled_count=self._cancelled_count,
                average_execution_time_ms=avg_time,
                total_steps_executed=self._total_steps_executed,
                active_workflows=0,
                metadata={"thread_safety": "PROTECTED"},
            )

    def clear(self) -> None:
        """Reset workflow statistics counters."""
        with self._lock:
            self._total_workflows = 0
            self._completed_count = 0
            self._failed_count = 0
            self._cancelled_count = 0
            self._total_execution_time_ms = 0.0
            self._total_steps_executed = 0
