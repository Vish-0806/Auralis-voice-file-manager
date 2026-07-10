"""Sequential workflow step execution management."""

from __future__ import annotations

import logging
import time
from typing import Any
from core.models import ExecutionPlan, ExecutionResult
from .models import WorkflowDefinition


class WorkflowExecutor:
    """Orchestrates multi-step workflow sequential execution and tracks logs for rollbacks."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the WorkflowExecutor.

        Args:
            logger: Optional logger for executor context.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._history_logs: list[dict[str, Any]] = []

    def execute(self, workflow: WorkflowDefinition, dispatcher: Any) -> ExecutionResult:
        """Runs the workflow steps sequentially.

        Args:
            workflow: The workflow definition schema.
            dispatcher: ActionDispatcher instance.

        Returns:
            An ExecutionResult indicating final status.
        """

        self._logger.info("Starting workflow sequential execution", extra={"name": workflow.name})
        self._history_logs.clear()
        start_time = time.perf_counter()

        for idx, step in enumerate(workflow.steps):
            self._logger.info(
                "Executing workflow step",
                extra={"step_idx": idx, "intent": step.intent.value},
            )

            sub_plan = ExecutionPlan(
                intent=step.intent,
                target=step.target,
                parameters=step.parameters,
                confidence=1.0,
            )

            try:
                result = dispatcher.dispatch(sub_plan)
                
                self._history_logs.append({
                    "step_idx": idx,
                    "plan": {
                        "intent": sub_plan.intent.value,
                        "target": sub_plan.target,
                        "parameters": sub_plan.parameters,
                    },
                    "success": result.success,
                    "response": result.response,
                })

                if not result.success:
                    self._logger.error(
                        "Workflow step execution failed, stopping sequence",
                        extra={"step_idx": idx, "error": result.error},
                    )
                    return ExecutionResult(
                        success=False,
                        response=f"Workflow step {idx} ({step.intent.value}) failed: {result.response}",
                        error=result.error or "Step failure",
                        execution_time=time.perf_counter() - start_time,
                    )

            except Exception as exc:
                self._logger.error("Workflow executor encountered exception", exc_info=exc)
                return ExecutionResult(
                    success=False,
                    response=f"Workflow step {idx} ({step.intent.value}) raised exception: {str(exc)}",
                    error=str(exc),
                    execution_time=time.perf_counter() - start_time,
                )

        self._logger.info("Workflow completed successfully", extra={"name": workflow.name})
        return ExecutionResult(
            success=True,
            response=f"Workflow '{workflow.name}' completed successfully.",
            data={"history_steps_count": len(self._history_logs)},
            execution_time=time.perf_counter() - start_time,
        )

    @property
    def history_logs(self) -> list[dict[str, Any]]:
        """Returns execution logs history for rollback audits."""

        return self._history_logs
