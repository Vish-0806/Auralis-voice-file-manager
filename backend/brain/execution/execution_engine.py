"""Execution Engine coordinator running routed execution plans through Auralis dispatcher."""

from __future__ import annotations

import logging
import uuid
import time
from typing import Any

# pyrefly: ignore [missing-import]
from brain.capability.models import RoutedExecutionPlan
from brain.capability.capability_matcher import CapabilityMatcher
from brain.recovery.recovery_engine import RecoveryEngine
from brain.monitoring.progress_monitor import ProgressMonitor
from automation.workflow.workflow_registry import WorkflowRegistry
from core.models import ExecutionPlan as CoreExecutionPlan
from core.intents import Intent

from .models import ExecutionSummary, ExecutionRecord, ExecutionStatus
from .execution_context import ExecutionContext
from .execution_history import ExecutionHistory
from .execution_validator import ExecutionValidator
from .execution_scheduler import ExecutionScheduler


class ExecutionEngine:
    """Coordinates and executes plan steps sequentially through the system dispatcher."""

    def __init__(
        self,
        validator: ExecutionValidator | None = None,
        scheduler: ExecutionScheduler | None = None,
        history: ExecutionHistory | None = None,
        recovery_engine: RecoveryEngine | None = None,
        progress_monitor: ProgressMonitor | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the ExecutionEngine.

        Args:
            validator: Plan integrity checker.
            scheduler: Sequence task scheduler.
            history: Session history logger.
            recovery_engine: Injected RecoveryEngine instance.
            progress_monitor: Injected ProgressMonitor instance.
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._validator = validator or ExecutionValidator(logger=self._logger)
        self._scheduler = scheduler or ExecutionScheduler(logger=self._logger)
        self._history = history or ExecutionHistory(logger=self._logger)
        self._matcher = CapabilityMatcher(logger=self._logger)
        self._recovery_engine = recovery_engine or RecoveryEngine(logger=self._logger)
        self._progress_monitor = progress_monitor or ProgressMonitor(logger=self._logger)

    def execute_plan(self, plan: RoutedExecutionPlan, dispatcher: Any) -> ExecutionSummary:
        """Validates and executes a RoutedExecutionPlan step-by-step through the dispatcher.

        Args:
            plan: The RoutedExecutionPlan to run.
            dispatcher: ActionDispatcher instance.

        Returns:
            An ExecutionSummary detailing the run results.
        """
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        self._logger.info("Starting execution session", extra={"execution_id": execution_id, "intent": plan.intent.value})

        try:
            self._validator.validate_plan(plan, dispatcher)
        except Exception as val_err:
            self._logger.error("Plan validation failed", exc_info=val_err)
            return ExecutionSummary(
                execution_id=execution_id,
                success=False,
                records=[],
                total_duration=0.0,
                error=f"Validation failed: {str(val_err)}",
            )

        context = ExecutionContext(execution_id=execution_id, logger=self._logger)
        session_start_time = time.perf_counter()
        records: list[ExecutionRecord] = []
        overall_success = True
        summary_error = None

        scheduled_routes = self._scheduler.schedule_steps(plan.routes)
        
        step_ids = [route.step_id or "main" for route in scheduled_routes]
        self._progress_monitor.start_session(execution_id, step_ids)

        steps_map = {}
        if plan.intent == Intent.RUN_WORKFLOW and plan.target:
            registry = WorkflowRegistry(logger=self._logger)
            wf_def = registry.get_workflow(plan.target)
            if wf_def:
                for idx, step in enumerate(wf_def.steps):
                    step_id = f"step_{idx + 1}"
                    steps_map[step_id] = {
                        "intent": step.intent,
                        "target": step.target,
                        "parameters": step.parameters,
                    }
        
        if not steps_map:
            for route in plan.routes:
                steps_map[route.step_id or "main"] = {
                    "intent": route.intent,
                    "target": plan.target,
                    "parameters": plan.parameters,
                }

        for route in scheduled_routes:
            step_id = route.step_id or "main"
            step_data = steps_map.get(step_id)
            if not step_data:
                self._logger.warning("Step data not found in plan maps", extra={"step_id": step_id})
                continue

            context.start_step(step_id, route.capability_name)
            step_start_time = time.perf_counter()

            step_plan = CoreExecutionPlan(
                intent=step_data["intent"],
                target=step_data["target"],
                parameters=step_data["parameters"],
                confidence=plan.confidence,
            )

            self._logger.debug(
                "Dispatching step execution plan",
                extra={
                    "execution_id": execution_id,
                    "step_id": step_id,
                    "intent": step_plan.intent.value,
                    "capability": route.capability_name,
                },
            )

            step_status = ExecutionStatus.SUCCESS
            step_response = None
            step_error = None

            self._progress_monitor.start_step(step_id)

            try:
                result = dispatcher.dispatch(step_plan)
                duration = result.execution_time
                if not result.success:
                    step_status = ExecutionStatus.FAILED
                    step_error = result.error or "Capability execution reported failure"
                    step_response = result.response
                else:
                    step_response = result.response
                    context.complete_step(step_id, {"response": result.response, "data": result.data})
                    self._progress_monitor.complete_step(step_id, duration)
            except Exception as disp_err:
                duration = time.perf_counter() - step_start_time
                step_status = ExecutionStatus.FAILED
                step_error = str(disp_err)
                self._logger.error("Dispatcher encountered execution exception", exc_info=disp_err)

            record = ExecutionRecord(
                step_id=step_id,
                intent=step_plan.intent,
                capability=route.capability_name,
                status=step_status,
                duration=duration,
                response=step_response,
                error=step_error,
            )

            self._history.record_step(record)
            records.append(record)

            if step_status == ExecutionStatus.FAILED:
                self._progress_monitor.fail_step(step_id, duration)

                self._logger.info("Attempting automatic self-correction and recovery", extra={"step_id": step_id})
                self._progress_monitor.start_recovery()

                recovery_result = self._recovery_engine.recover(
                    step_id=step_id,
                    intent=step_plan.intent,
                    target=step_plan.target,
                    parameters=step_plan.parameters,
                    error_message=step_error or "",
                    dispatcher=dispatcher,
                )

                self._progress_monitor.finish_recovery(success=recovery_result.success)

                if recovery_result.success:
                    self._logger.info("Step recovery resolved successfully. Continuing execution loop.", extra={"step_id": step_id})
                    step_status = ExecutionStatus.SUCCESS
                    step_error = None
                    step_response = f"Recovered via strategy: {recovery_result.strategy_applied}"
                    
                    context.complete_step(step_id, {"recovered": True, "strategy": recovery_result.strategy_applied})

                    record.status = ExecutionStatus.SUCCESS
                    record.response = step_response
                    record.error = None
                else:
                    self._logger.warning(
                        "Sequential execution aborted due to step failure",
                        extra={"failed_step_id": step_id, "error": step_error},
                    )
                    overall_success = False
                    summary_error = f"Step '{step_id}' failed: {step_error}. Recovery failed: {recovery_result.error}"
                    break

        total_duration = time.perf_counter() - session_start_time
        summary = ExecutionSummary(
            execution_id=execution_id,
            success=overall_success,
            records=records,
            total_duration=total_duration,
            error=summary_error,
        )

        self._progress_monitor.complete_session(success=overall_success, total_duration=total_duration)

        self._logger.info(
            "Execution session completed",
            extra={
                "execution_id": execution_id,
                "success": overall_success,
                "records_count": len(records),
                "duration_ms": int(total_duration * 1000),
            },
        )
        return summary
