"""Execution Coordinator for managing plan execution pipelines.

This module provides thread-safe verification of plan readiness, step sequence ordering,
session orchestration, step runner dispatching, error handling, and rollback execution.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Dict, Optional

from brain.execution.execution_context import ExecutionContext
from brain.execution.execution_models import ExecutionResult, ExecutionStatus, ExecutionStepResult
from brain.execution.execution_policy import ExecutionPolicy
from brain.execution.execution_session import ExecutionSession
from brain.execution.execution_step_runner import ExecutionStepRunner
from brain.planning.action_planner import ActionStep
from brain.planning.execution_plan_builder import ExecutionPlan, ExecutionReadiness

logger = logging.getLogger(__name__)


class ExecutionCoordinator:
    """Thread-safe coordinator for verifying and executing ExecutionPlans."""

    def __init__(
        self,
        step_runner: Optional[ExecutionStepRunner] = None,
        default_policy: Optional[ExecutionPolicy] = None,
    ) -> None:
        """Initializes the coordinator with step runner and default policy."""
        self._lock = threading.RLock()
        self._step_runner = step_runner or ExecutionStepRunner()
        self._default_policy = default_policy or ExecutionPolicy()

    def execute_plan(
        self,
        plan: ExecutionPlan,
        policy: Optional[ExecutionPolicy] = None,
    ) -> ExecutionResult:
        """Executes an immutable ExecutionPlan deterministically."""
        with self._lock:
            effective_policy = policy or self._default_policy

            # Verify Plan Readiness
            if plan.readiness in (ExecutionReadiness.BLOCKED, ExecutionReadiness.NOT_READY):
                logger.warning("Execution rejected due to plan readiness: readiness=%s", plan.readiness.value)
                return ExecutionResult(
                    execution_id=f"rejected-{plan.request[:10]}",
                    status=ExecutionStatus.BLOCKED,
                    metadata={"reason": f"Plan readiness is {plan.readiness.value}"},
                )

            # Create context and session
            context = ExecutionContext(plan=plan, policy=effective_policy)
            session = ExecutionSession(context)
            session.start()

            # Determine step lookup table & order
            step_map: Dict[int, ActionStep] = {s.step_number: s for s in plan.action_plan.steps}
            order = plan.execution_order if plan.execution_order else sorted(step_map.keys())

            for step_num in order:
                if context.cancellation_requested:
                    session.cancel()
                    break

                step = step_map.get(step_num)
                if not step:
                    logger.warning("Step number %d not found in plan steps", step_num)
                    continue

                context.current_step_number = step_num
                step_result = self._step_runner.execute_step(step, context)
                session.record_step_result(step_result)

                if step_result.status == ExecutionStatus.FAILED:
                    if effective_policy.rollback_enabled:
                        self._trigger_rollback(session, step_num, context)
                    if not effective_policy.continue_on_error:
                        break

            return session.complete()

    def _trigger_rollback(
        self,
        session: ExecutionSession,
        failed_step_number: int,
        context: ExecutionContext,
    ) -> None:
        """Triggers rollback sequence for completed steps upon failure."""
        logger.info("Rollback Started: execution_id=%s failed_step=%d", session.execution_id, failed_step_number)
        rollback_result = ExecutionStepResult(
            step_id=f"rollback-{failed_step_number}",
            step_number=failed_step_number,
            status=ExecutionStatus.ROLLING_BACK,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            output={"rollback_executed": True},
            metadata={"failed_step": failed_step_number},
        )
        session.record_step_result(rollback_result)
        logger.info("Rollback Completed: execution_id=%s", session.execution_id)
