"""Workflow Executor for the Auralis Workflow Execution Engine (Phase 12.4).

Executes scheduled workflow steps in topological dependency order.
Coordinates with the Command Execution Orchestrator, tracks step outputs, and handles retries/cancellations.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional, Set

from brain.execution.workflow.exceptions import WorkflowCancellationError, WorkflowExecutionError
from brain.execution.workflow.interfaces import IWorkflowExecutor
from brain.execution.workflow.workflow_models import (
    WorkflowExecution,
    WorkflowPriority,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepStatus,
)

logger = logging.getLogger(__name__)


class WorkflowExecutor(IWorkflowExecutor):
    """Executor coordinating scheduled workflow step execution, retries, and output passing."""

    def __init__(
        self,
        command_orchestrator: Optional[Any] = None,
        planning_runtime: Optional[Any] = None,
        security_runtime: Optional[Any] = None,
        os_runtime: Optional[Any] = None,
    ) -> None:
        """Initializes WorkflowExecutor with optional injected subsystem runtimes."""
        self._command_orchestrator = command_orchestrator
        self._planning_runtime = planning_runtime
        self._security_runtime = security_runtime
        self._os_runtime = os_runtime

    def execute(
        self,
        execution: WorkflowExecution,
        request: WorkflowRequest,
        cancellation_token: Optional[Dict[str, bool]] = None,
    ) -> WorkflowResult:
        """Execute a scheduled workflow graph end-to-end.

        Args:
            execution: WorkflowExecution schedule object.
            request: Original WorkflowRequest.
            cancellation_token: Optional dict token with key "cancelled": True.

        Returns:
            WorkflowResult model.

        Raises:
            WorkflowExecutionError: If workflow execution encounters an unrecoverable error.
        """
        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)
        step_map = {step.step_id: step for step in request.steps}

        updated_steps: List[WorkflowStep] = []
        step_outputs: Dict[str, Dict[str, Any]] = {}
        failed_step_ids: Set[str] = set()
        skipped_step_ids: Set[str] = set()

        completed_count = 0
        failed_count = 0
        overall_status = WorkflowStatus.COMPLETED

        for step_id in execution.execution_order:
            # Check cancellation token
            if cancellation_token and cancellation_token.get("cancelled", False):
                overall_status = WorkflowStatus.CANCELLED
                logger.info("Workflow execution cancelled at step '%s'", step_id)
                break

            orig_step = step_map[step_id]

            # Check if any hard dependency of this step failed or was skipped
            failed_deps = [dep for dep in orig_step.dependencies if dep in failed_step_ids or dep in skipped_step_ids]
            if failed_deps:
                skipped_step_ids.add(step_id)
                skipped_step = WorkflowStep(
                    step_id=orig_step.step_id,
                    name=orig_step.name,
                    action_type=orig_step.action_type,
                    prompt_or_payload=orig_step.prompt_or_payload,
                    status=WorkflowStepStatus.SKIPPED,
                    dependencies=list(orig_step.dependencies),
                    priority=orig_step.priority,
                    retries_left=orig_step.max_retries,
                    max_retries=orig_step.max_retries,
                    output={},
                    error=f"Skipped because dependency step(s) failed or were skipped: {', '.join(failed_deps)}",
                    metadata={"skipped_due_to": failed_deps},
                )
                updated_steps.append(skipped_step)
                continue

            step_output: Dict[str, Any] = {}
            step_error: Optional[str] = None
            step_status = WorkflowStepStatus.COMPLETED

            # Retries execution loop
            max_attempts = max(1, orig_step.max_retries + 1)
            attempt = 0
            success = False

            while attempt < max_attempts and not success:
                attempt += 1
                try:
                    # Pass context outputs from dependent steps
                    dep_context = {
                        dep_id: step_outputs[dep_id]
                        for dep_id in orig_step.dependencies
                        if dep_id in step_outputs
                    }

                    prompt_payload = orig_step.prompt_or_payload
                    if isinstance(prompt_payload, str) and not prompt_payload:
                        prompt_payload = orig_step.name or f"Execute step {orig_step.step_id}"

                    if self._command_orchestrator and hasattr(self._command_orchestrator, "orchestrate"):
                        orch_res = self._command_orchestrator.orchestrate(
                            prompt_payload,
                            context={"dependent_outputs": dep_context},
                        )
                        step_output = dict(getattr(orch_res, "output", {}))
                    else:
                        step_output = {
                            "step_id": orig_step.step_id,
                            "action": orig_step.action_type,
                            "result": f"Executed '{orig_step.name or orig_step.step_id}'",
                            "dependent_outputs": dep_context,
                        }

                    success = True

                except Exception as exc:
                    step_error = str(exc)
                    logger.warning("Step '%s' attempt %d failed: %s", step_id, attempt, exc)
                    if attempt >= max_attempts:
                        step_status = WorkflowStepStatus.FAILED
                        failed_count += 1
                        failed_step_ids.add(step_id)
                        overall_status = WorkflowStatus.FAILED

            if success:
                completed_count += 1
                step_outputs[step_id] = step_output

            executed_step = WorkflowStep(
                step_id=orig_step.step_id,
                name=orig_step.name,
                action_type=orig_step.action_type,
                prompt_or_payload=orig_step.prompt_or_payload,
                status=step_status,
                dependencies=list(orig_step.dependencies),
                priority=orig_step.priority,
                retries_left=max(0, orig_step.max_retries - attempt + 1),
                max_retries=orig_step.max_retries,
                output=step_output,
                error=step_error,
                metadata={"attempts": attempt},
            )
            updated_steps.append(executed_step)

            if step_status == WorkflowStepStatus.FAILED and orig_step.priority == WorkflowPriority.CRITICAL:
                logger.error("Critical step '%s' failed. Aborting remaining workflow.", step_id)
                break

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return WorkflowResult(
            workflow_id=request.request_id,
            execution_id=execution.execution_id,
            status=overall_status,
            step_results=updated_steps,
            completed_steps=completed_count,
            failed_steps=failed_count,
            total_steps=len(request.steps),
            execution_time_ms=elapsed_ms,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            metadata={"ordered_steps_processed": len(updated_steps)},
        )
