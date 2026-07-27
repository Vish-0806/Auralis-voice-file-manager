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
from .execution_state_manager import ExecutionStateManager
from .decision_engine import DecisionEngine, DecisionContext, DecisionType, DecisionReason, ExecutionDecision
from .failure_recovery import FailureRecoveryEngine, RecoveryContext


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
        workflow_observer: Any = None,
        state_manager: ExecutionStateManager | None = None,
        decision_engine: DecisionEngine | None = None,
        failure_recovery_engine: FailureRecoveryEngine | None = None,
    ) -> None:
        """Initializes the ExecutionEngine.

        Args:
            validator: Plan integrity checker.
            scheduler: Sequence task scheduler.
            history: Session history logger.
            recovery_engine: Injected RecoveryEngine instance.
            progress_monitor: Injected ProgressMonitor instance.
            logger: Optional custom logger.
            workflow_observer: Optional injected WorkflowObserver instance.
            state_manager: Optional injected ExecutionStateManager.
            decision_engine: Optional injected DecisionEngine.
            failure_recovery_engine: Optional injected FailureRecoveryEngine.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._validator = validator or ExecutionValidator(logger=self._logger)
        self._scheduler = scheduler or ExecutionScheduler(logger=self._logger)
        self._history = history or ExecutionHistory(logger=self._logger)
        self._matcher = CapabilityMatcher(logger=self._logger)
        self._recovery_engine = recovery_engine or RecoveryEngine(logger=self._logger)
        self._progress_monitor = progress_monitor or ProgressMonitor(logger=self._logger)
        self._state_manager = state_manager or ExecutionStateManager()
        self._decision_engine = decision_engine or DecisionEngine()
        self._failure_recovery_engine = failure_recovery_engine or FailureRecoveryEngine()

        # Inject or dynamically build default WorkflowObserver
        self._workflow_observer = workflow_observer
        if self._workflow_observer is None:
            try:
                from memory import MemoryService
                from memory.workflows import WorkflowObserver, SequenceBuilder, ObservationRepository
                mem_service = MemoryService()
                provider = getattr(mem_service._manager._repository, "_provider", None)
                if provider:
                    self._workflow_observer = WorkflowObserver(SequenceBuilder(), ObservationRepository(provider))
            except Exception as e:
                self._logger.warning("Could not initialize default WorkflowObserver in ExecutionEngine", exc_info=e)

    def _safe_create_execution(self, execution_id: str, user_id: int, workflow_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        try:
            self._state_manager.create_execution(execution_id, user_id, workflow_id, metadata)
            self._logger.info("Execution Created", extra={"execution_id": execution_id})
        except Exception as e:
            self._logger.error("Failed to create execution in state manager", exc_info=e)

    def _safe_mark_running(self, execution_id: str) -> None:
        try:
            self._state_manager.mark_running(execution_id)
            self._logger.info("Execution Running", extra={"execution_id": execution_id})
        except Exception as e:
            self._logger.error("Failed to mark execution running in state manager", exc_info=e)

    def _safe_update_progress(
        self,
        execution_id: str,
        percentage: float,
        current_step: int,
        total_steps: int,
        current_operation: str | None = None,
        estimated_remaining_seconds: float | None = None,
    ) -> None:
        try:
            self._state_manager.update_progress(
                execution_id=execution_id,
                percentage=percentage,
                current_step=current_step,
                total_steps=total_steps,
                current_operation=current_operation,
                estimated_remaining_seconds=estimated_remaining_seconds,
            )
            self._logger.info("Execution Progress Updated", extra={"execution_id": execution_id, "percentage": percentage})
        except Exception as e:
            self._logger.error("Failed to update progress in state manager", exc_info=e)

    def _safe_mark_completed(self, execution_id: str) -> None:
        try:
            self._state_manager.mark_completed(execution_id)
            self._logger.info("Execution Completed", extra={"execution_id": execution_id})
        except Exception as e:
            self._logger.error("Failed to mark execution completed in state manager", exc_info=e)

    def _safe_mark_failed(self, execution_id: str, error_message: str) -> None:
        try:
            self._state_manager.mark_failed(execution_id, error_message)
            self._logger.info("Execution Failed", extra={"execution_id": execution_id, "error": error_message})
        except Exception as e:
            self._logger.error("Failed to mark execution failed in state manager", exc_info=e)

    def _safe_mark_retrying(self, execution_id: str) -> None:
        try:
            self._state_manager.mark_retrying(execution_id)
            self._logger.info("Execution Retrying", extra={"execution_id": execution_id})
        except Exception as e:
            self._logger.error("Failed to mark execution retrying in state manager", exc_info=e)

    def _safe_mark_cancelled(self, execution_id: str) -> None:
        try:
            self._state_manager.mark_cancelled(execution_id)
            self._logger.info("Execution Cancelled", extra={"execution_id": execution_id})
        except Exception as e:
            self._logger.error("Failed to mark execution cancelled in state manager", exc_info=e)

    def _safe_mark_paused(self, execution_id: str) -> None:
        try:
            self._state_manager.mark_paused(execution_id)
            self._logger.info("Execution Paused", extra={"execution_id": execution_id})
        except Exception as e:
            self._logger.error("Failed to mark execution paused in state manager", exc_info=e)

    def _safe_mark_waiting(self, execution_id: str) -> None:
        try:
            state = self._state_manager.get_execution(execution_id)
            if state:
                from .execution_state import ExecutionStatus as StateStatus
                state.status = StateStatus.WAITING
                state._touch()
            self._logger.info("Execution Waiting", extra={"execution_id": execution_id})
        except Exception as e:
            self._logger.error("Failed to mark execution waiting in state manager", exc_info=e)

    def _safe_evaluate_decision(self, context: DecisionContext) -> ExecutionDecision:
        try:
            decision = self._decision_engine.evaluate(context)
            self._logger.info(
                "Decision Evaluated",
                extra={
                    "execution_id": context.execution_state.execution_id if context.execution_state else None,
                    "decision_type": decision.decision_type.value,
                    "reason": decision.reason.value,
                }
            )
            return decision
        except Exception as e:
            self._logger.error("DecisionEngine evaluation failed, default to EXECUTE", exc_info=e)
            return ExecutionDecision(
                decision_type=DecisionType.EXECUTE,
                reason=DecisionReason.UNKNOWN,
                confidence=1.0,
                message="Decision engine evaluation failure fallback to EXECUTE.",
            )

    def _safe_analyse_and_record_failure(
        self,
        execution_id: str,
        step_id: str,
        step_plan: CoreExecutionPlan,
        plan_parameters: dict,
        exception: Exception,
    ) -> None:
        try:
            exec_state = self._state_manager.get_execution(execution_id)
            retry_count = exec_state.retry_count if exec_state else 0
            
            # 1. Build RecoveryContext
            context = RecoveryContext(
                execution_state=exec_state,
                execution_step=step_plan,
                resolved_preferences=plan_parameters.get("resolved_preferences") or plan_parameters,
                exception=exception,
                retry_count=retry_count,
            )

            # 2. Pass context to build_recovery_plan
            plan = self._failure_recovery_engine.build_recovery_plan(context)
            analysis = self._failure_recovery_engine.analyse_failure(context)

            # 3. Attach recovery info to execution metadata
            if exec_state:
                exec_state.metadata["failure_category"] = analysis.failure_category.value
                exec_state.metadata["recovery_strategy"] = plan.strategy.value
                exec_state.metadata["recovery_reason"] = plan.reason
                exec_state.metadata["recovery_confidence"] = analysis.confidence
                exec_state.metadata["recoverable"] = analysis.recoverable

            # 4. Log structured events
            self._logger.info("Recovery Analysis Completed", extra={"execution_id": execution_id})
            self._logger.info("Failure Category", extra={"execution_id": execution_id, "category": analysis.failure_category.value})
            self._logger.info("Recovery Strategy Selected", extra={"execution_id": execution_id, "strategy": plan.strategy.value})
            self._logger.info("Recoverable", extra={"execution_id": execution_id, "recoverable": analysis.recoverable})
            self._logger.info("Recovery Deferred", extra={"execution_id": execution_id})

        except Exception as e:
            self._logger.warning("FailureRecoveryEngine encountered execution exception", exc_info=e)

    def _run_async(self, coro) -> Any:
        """Runs a coroutine synchronously or schedules it on a running event loop."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            return loop.create_task(coro)
        else:
            return loop.run_until_complete(coro)

    def execute_plan(self, plan: RoutedExecutionPlan, dispatcher: Any, user_id: int = 0) -> ExecutionSummary:
        """Validates and executes a RoutedExecutionPlan step-by-step through the dispatcher.

        Args:
            plan: The RoutedExecutionPlan to run.
            dispatcher: ActionDispatcher instance.

        Returns:
            An ExecutionSummary detailing the run results.
        """
        # Determine execution_id
        execution_id = None
        if isinstance(plan.parameters, dict):
            execution_id = plan.parameters.get("execution_id")
            if not execution_id:
                metadata = plan.parameters.get("metadata")
                if isinstance(metadata, dict):
                    execution_id = metadata.get("execution_id")
            if not execution_id:
                req_metadata = plan.parameters.get("request_metadata")
                if isinstance(req_metadata, dict):
                    execution_id = req_metadata.get("execution_id")

        if not execution_id:
            try:
                execution_id = str(uuid.UUID(plan.execution_id))
            except Exception:
                execution_id = str(uuid.uuid4())

        self._logger.info("Starting execution session", extra={"execution_id": execution_id, "intent": plan.intent.value})

        # Register execution and start running
        workflow_id = plan.target if plan.intent == Intent.RUN_WORKFLOW else None
        self._safe_create_execution(
            execution_id=execution_id,
            user_id=user_id,
            workflow_id=workflow_id,
            metadata=plan.parameters,
        )
        self._safe_mark_running(execution_id)

        try:
            self._validator.validate_plan(plan, dispatcher)
        except Exception as val_err:
            self._logger.error("Plan validation failed", exc_info=val_err)
            self._safe_mark_failed(execution_id, f"Validation failed: {str(val_err)}")
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
        total_steps = len(scheduled_routes)
        
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

        for i, route in enumerate(scheduled_routes):
            step_id = route.step_id or "main"
            step_data = steps_map.get(step_id)
            if not step_data:
                self._logger.warning("Step data not found in plan maps", extra={"step_id": step_id})
                continue

            # Update progress before step begins
            percentage = (i / total_steps * 100.0) if total_steps > 0 else 0.0
            self._safe_update_progress(
                execution_id=execution_id,
                percentage=percentage,
                current_step=i + 1,
                total_steps=total_steps,
                current_operation=step_id,
            )

            context.start_step(step_id, route.capability_name)
            step_start_time = time.perf_counter()

            step_plan = CoreExecutionPlan(
                intent=step_data["intent"],
                target=step_data["target"],
                parameters=step_data["parameters"],
                confidence=plan.confidence,
            )

            # Build decision context for this step
            exec_state = self._state_manager.get_execution(execution_id)
            decision_context = DecisionContext(
                execution_state=exec_state,
                resolved_preferences=plan.parameters.get("resolved_preferences") or plan.parameters,
                workflow_metadata={
                    "intent": step_plan.intent.value if hasattr(step_plan.intent, "value") else str(step_plan.intent),
                    "target": step_plan.target,
                    "parameters": step_plan.parameters,
                    "dangerous_operation": step_plan.parameters.get("dangerous_operation"),
                    "missing_dependency": step_plan.parameters.get("missing_dependency"),
                    "dependency_name": step_plan.parameters.get("dependency_name"),
                },
                capability_metadata={
                    "vscode_running": step_plan.parameters.get("vscode_running"),
                    "app_already_running": step_plan.parameters.get("app_already_running"),
                    "app_name": step_plan.parameters.get("app_name"),
                    "missing_executable": step_plan.parameters.get("missing_executable"),
                    "original_executable": step_plan.parameters.get("original_executable"),
                    "fallback_executable": step_plan.parameters.get("fallback_executable"),
                }
            )

            # Evaluate decision safely
            decision = self._safe_evaluate_decision(decision_context)

            # Internally retain decision metadata in the execution state
            if exec_state:
                try:
                    exec_state.metadata["decision_type"] = decision.decision_type.value
                    exec_state.metadata["decision_reason"] = decision.reason.value
                    exec_state.metadata["decision_confidence"] = decision.confidence
                    exec_state.metadata["decision_metadata"] = decision.metadata
                except Exception:
                    pass

            # Handle decisions
            if decision.decision_type == DecisionType.CANCEL:
                self._logger.info("Decision Applied", extra={"execution_id": execution_id, "decision": "CANCEL"})
                self._logger.info("Execution Cancelled", extra={"execution_id": execution_id})
                self._safe_mark_cancelled(execution_id)
                overall_success = False
                summary_error = f"Execution cancelled: {decision.message}"
                break

            elif decision.decision_type == DecisionType.WAIT:
                self._logger.info("Decision Applied", extra={"execution_id": execution_id, "decision": "WAIT"})
                self._safe_mark_waiting(execution_id)
                overall_success = False
                summary_error = f"Execution waiting: {decision.message}"
                break

            elif decision.decision_type == DecisionType.ASK_USER:
                self._logger.info("Decision Applied", extra={"execution_id": execution_id, "decision": "ASK_USER"})
                self._logger.info("Confirmation Required", extra={"execution_id": execution_id})
                self._safe_mark_paused(execution_id)
                overall_success = False
                summary_error = f"User confirmation required: {decision.message}"
                break

            elif decision.decision_type == DecisionType.SKIP:
                self._logger.info("Decision Applied", extra={"execution_id": execution_id, "decision": "SKIP"})
                # Skip executing capability dispatch, treat step as successful
                duration = 0.0
                step_status = ExecutionStatus.SUCCESS
                step_response = f"Step skipped: {decision.message}"
                step_error = None
                
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

                # Update progress after completed step
                percentage = (((i + 1) / total_steps) * 100.0) if total_steps > 0 else 100.0
                self._safe_update_progress(
                    execution_id=execution_id,
                    percentage=percentage,
                    current_step=i + 1,
                    total_steps=total_steps,
                    current_operation=step_id,
                )
                continue

            elif decision.decision_type == DecisionType.REUSE_RESOURCE:
                self._logger.info("Decision Applied", extra={"execution_id": execution_id, "decision": "REUSE_RESOURCE"})
                self._logger.info("Resource Reused", extra={"execution_id": execution_id})
                # Skip executing capability dispatch, treat step as successful
                duration = 0.0
                step_status = ExecutionStatus.SUCCESS
                step_response = f"Resource reused: {decision.message}"
                step_error = None

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

                # Update progress after completed step
                percentage = (((i + 1) / total_steps) * 100.0) if total_steps > 0 else 100.0
                self._safe_update_progress(
                    execution_id=execution_id,
                    percentage=percentage,
                    current_step=i + 1,
                    total_steps=total_steps,
                    current_operation=step_id,
                )
                continue

            elif decision.decision_type == DecisionType.USE_FALLBACK:
                self._logger.info("Decision Applied", extra={"execution_id": execution_id, "decision": "USE_FALLBACK"})
                self._logger.info("Fallback Selected", extra={"execution_id": execution_id})
                if decision.recommended_action:
                    # Swapping executable target
                    step_plan.target = decision.metadata.get("fallback") or decision.recommended_action.split()[-1]

            elif decision.decision_type == DecisionType.RETRY:
                self._logger.info("Decision Applied", extra={"execution_id": execution_id, "decision": "RETRY"})
                self._safe_mark_retrying(execution_id)

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
            disp_err = None

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
            except Exception as e:
                disp_err = e
                duration = time.perf_counter() - step_start_time
                step_status = ExecutionStatus.FAILED
                step_error = str(e)
                self._logger.error("Dispatcher encountered execution exception", exc_info=e)

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
                # Trigger failure analysis and record it
                exc = disp_err if disp_err is not None else RuntimeError(step_error or "Unknown failure")
                self._safe_analyse_and_record_failure(
                    execution_id=execution_id,
                    step_id=step_id,
                    step_plan=step_plan,
                    plan_parameters=plan.parameters,
                    exception=exc,
                )

                self._progress_monitor.fail_step(step_id, duration)

                self._logger.info("Attempting automatic self-correction and recovery", extra={"step_id": step_id})
                self._progress_monitor.start_recovery()

                self._safe_mark_retrying(execution_id)

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
                    self._safe_mark_failed(execution_id, summary_error)
                    break

            if step_status == ExecutionStatus.SUCCESS:
                # Update progress after completed/recovered step
                percentage = (((i + 1) / total_steps) * 100.0) if total_steps > 0 else 100.0
                self._safe_update_progress(
                    execution_id=execution_id,
                    percentage=percentage,
                    current_step=i + 1,
                    total_steps=total_steps,
                    current_operation=step_id,
                )

        if overall_success:
            self._safe_mark_completed(execution_id)

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

        # Trigger User Preference Learning
        try:
            from datetime import datetime, timezone
            from memory import MemoryEntry, MemoryMetadata, MemoryType, MemoryService
            from memory.preferences import (
                PreferenceObservation,
                PreferenceLearningCoordinator,
                PreferenceLearner,
                PreferenceScorer,
                PreferenceConflictResolver
            )

            self._logger.info("Preference Learning Triggered", extra={"user_id": user_id, "execution_id": execution_id})

            # Create PreferenceObservation objects and log them
            observed_categories = set()
            obs_payloads = []
            
            for record in records:
                step_data = steps_map.get(record.step_id) if 'steps_map' in locals() else None
                params = step_data.get("parameters") if step_data else {}
                for category, param_key in [("Shell", "shell"), ("Browser", "browser"), ("IDE", "ide")]:
                    val = params.get(param_key) if params else None
                    if val and (category, val) not in observed_categories:
                        self._logger.info("Preference Observation Recorded", extra={"category": category, "value": val, "user_id": user_id})
                        observed_categories.add((category, val))
                        obs_payloads.append({
                            "category": category,
                            "value": val,
                            "is_override": False
                        })

            mem_service = MemoryService()
            
            activity_entry = MemoryEntry(
                id=execution_id + "_activity",
                content=f"Execution completed for plan: {plan.intent.value}",
                memory_type=MemoryType.ACTIVITY,
                metadata=MemoryMetadata(
                    created_at=datetime.now(timezone.utc),
                    additional_info={
                        "status": "COMPLETED" if overall_success else "FAILED",
                        "duration_ms": int(total_duration * 1000),
                        "input_parameters": plan.parameters or {},
                        "output_result": {"success": overall_success, "error": summary_error},
                        "user_id": user_id,
                        "preference_observation": obs_payloads[0] if obs_payloads else None
                    }
                )
            )
            self._run_async(mem_service.save(activity_entry))

            learner = PreferenceLearner()
            scorer = PreferenceScorer()
            conflict_resolver = PreferenceConflictResolver()
            learning_coordinator = PreferenceLearningCoordinator(
                learner=learner,
                scorer=scorer,
                conflict_resolver=conflict_resolver,
                memory_service=mem_service
            )
            self._run_async(learning_coordinator.process_new_execution(user_id, execution_id))

        except Exception as pref_err:
            self._logger.warning("Failed to trigger preference learning", exc_info=pref_err)

        # Trigger Workflow Observation
        try:
            if self._workflow_observer:
                step_obs_list = []
                for record in records:
                    step_data = steps_map.get(record.step_id) if 'steps_map' in locals() else None
                    params = step_data.get("parameters") if step_data else {}
                    from memory.workflows import WorkflowStepObservation
                    step_obs = WorkflowStepObservation(
                        step_id=record.step_id,
                        intent=record.intent.value if hasattr(record.intent, "value") else str(record.intent),
                        target=step_data.get("target") if step_data else None,
                        parameters=params or {},
                        status=record.status.value if hasattr(record.status, "value") else str(record.status),
                        duration_ms=record.duration * 1000.0,
                        timestamp=datetime.now(timezone.utc)
                    )
                    step_obs_list.append(step_obs)

                if step_obs_list:
                    obs_time = datetime.now(timezone.utc)
                    async def safe_observe():
                        try:
                            await self._workflow_observer.observe_execution(
                                user_id=user_id,
                                execution_id=execution_id,
                                steps=step_obs_list,
                                success=overall_success,
                                timestamp=obs_time,
                                context_metadata={"session_id": execution_id}
                            )
                        except Exception as inner_err:
                            self._logger.warning("Workflow observation recording encountered a failure", exc_info=inner_err)

                    self._run_async(safe_observe())
        except Exception as wf_err:
            self._logger.warning("Workflow observation recording encountered a failure", exc_info=wf_err)

        return summary
