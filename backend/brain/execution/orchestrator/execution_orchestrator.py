"""Execution Orchestrator for the Auralis Command Execution Orchestrator (Phase 12.3).

Master orchestrator coordinating stage execution across sub-runtimes:
1. INTENT_RESOLUTION
2. PLANNING (if planned mode required)
3. SECURITY_REVIEW
4. OS_EXECUTION
5. RESPONSE_SYNTHESIS

Contains ZERO OS or AI logic directly. Solely coordinates execution stages.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional

from brain.execution.orchestrator.exceptions import ExecutionCoordinationError
from brain.execution.orchestrator.execution_coordinator import ExecutionCoordinator
from brain.execution.orchestrator.execution_router import ExecutionRouter
from brain.execution.orchestrator.execution_tracker import ExecutionTracker
from brain.execution.orchestrator.interfaces import (
    IExecutionCoordinator,
    IExecutionOrchestrator,
    IExecutionRouter,
    IExecutionTracker,
)
from brain.execution.orchestrator.orchestrator_models import (
    ExecutionMode,
    ExecutionPlanReference,
    ExecutionResult,
    ExecutionStage,
    ExecutionStageType,
    ExecutionState,
    OrchestrationStatus,
)

logger = logging.getLogger(__name__)


class ExecutionOrchestrator(IExecutionOrchestrator):
    """Master orchestrator driving multi-stage execution coordination across subsystem runtimes."""

    def __init__(
        self,
        coordinator: Optional[IExecutionCoordinator] = None,
        router: Optional[IExecutionRouter] = None,
        tracker: Optional[IExecutionTracker] = None,
    ) -> None:
        """Initializes ExecutionOrchestrator with injected components."""
        self._coordinator = coordinator or ExecutionCoordinator()
        self._router = router or ExecutionRouter()
        self._tracker = tracker or ExecutionTracker()

    def orchestrate(
        self,
        request_or_prompt: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Coordinate multi-stage execution pipeline end-to-end.

        Args:
            request_or_prompt: Raw prompt, IntentResolution, or ExecutionRequest.
            context: Optional contextual parameters.

        Returns:
            Structured ExecutionResult model.

        Raises:
            ExecutionCoordinationError: If an unrecoverable orchestration exception occurs.
        """
        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)

        try:
            # 1. Prepare ExecutionContext via Coordinator
            exec_ctx = self._coordinator.prepare_execution(request_or_prompt, context=context)
            exec_id = self._tracker.start_execution(exec_ctx)

            stages: List[ExecutionStage] = []
            final_status = OrchestrationStatus.SUCCESS
            final_state = ExecutionState.COMPLETED
            overall_output: Dict[str, Any] = {}
            plan_ref: Optional[ExecutionPlanReference] = None
            error_msg: Optional[str] = None

            # Stage 1: INTENT_RESOLUTION
            stage_intent = self._router.route_stage(ExecutionStageType.INTENT_RESOLUTION, exec_ctx)
            stages.append(stage_intent)
            self._tracker.record_stage(exec_id, stage_intent)
            if stage_intent.output:
                overall_output.update(stage_intent.output)

            # Stage 2: PLANNING (Conditional on ExecutionMode)
            if exec_ctx.request.mode in (ExecutionMode.PLANNED, ExecutionMode.AI_GUIDED):
                stage_plan = self._router.route_stage(ExecutionStageType.PLANNING, exec_ctx)
                stages.append(stage_plan)
                self._tracker.record_stage(exec_id, stage_plan)
                if stage_plan.output:
                    overall_output.update(stage_plan.output)
                    plan_ref = ExecutionPlanReference(
                        step_count=1,
                        readiness="READY",
                        metadata=stage_plan.output.get("plan", {}),
                    )

            # Stage 3: SECURITY_REVIEW
            stage_sec = self._router.route_stage(ExecutionStageType.SECURITY_REVIEW, exec_ctx)
            stages.append(stage_sec)
            self._tracker.record_stage(exec_id, stage_sec)
            if stage_sec.output:
                overall_output.update(stage_sec.output)

            # Stage 4: OS_EXECUTION
            stage_os = self._router.route_stage(ExecutionStageType.OS_EXECUTION, exec_ctx)
            stages.append(stage_os)
            self._tracker.record_stage(exec_id, stage_os)
            if stage_os.output:
                overall_output.update(stage_os.output)

            if stage_os.status == OrchestrationStatus.FAILED:
                final_status = OrchestrationStatus.FAILED
                final_state = ExecutionState.FAILED
                error_msg = stage_os.error or "OS Execution stage failed"

            # Stage 5: RESPONSE_SYNTHESIS
            stage_resp = self._router.route_stage(ExecutionStageType.RESPONSE_SYNTHESIS, exec_ctx)
            stages.append(stage_resp)
            self._tracker.record_stage(exec_id, stage_resp)
            if stage_resp.output:
                overall_output.update(stage_resp.output)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result = ExecutionResult(
                execution_id=exec_id,
                status=final_status,
                state=final_state,
                stages=stages,
                plan_ref=plan_ref,
                output=overall_output,
                error=error_msg,
                execution_time_ms=elapsed_ms,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                metadata={"mode": exec_ctx.request.mode.value, "priority": exec_ctx.request.priority.value},
            )

            self._tracker.complete_execution(exec_id, result)
            return result

        except Exception as exc:
            logger.error("Execution orchestration failed: %s", exc)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                status=OrchestrationStatus.FAILED,
                state=ExecutionState.FAILED,
                error=str(exc),
                execution_time_ms=elapsed_ms,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )
