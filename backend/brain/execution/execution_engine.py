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
from .failure_recovery import FailureRecoveryEngine, RecoveryContext, RecoveryStrategy
from .clarification_engine import ClarificationEngine, ClarificationContext, ClarificationRequest
from .long_running_task_manager import LongRunningTaskManager, LongRunningTaskPriority
from .background_job_scheduler import BackgroundJobScheduler, convert_to_execution_request


def is_long_running_task(plan: Any) -> bool:

    """Determines whether an execution plan qualifies as a long-running task.

    Args:
        plan: The execution plan object.

    Returns:
        True if the plan matches long-running criteria, False otherwise.
    """
    if not plan:
        return False

    intent_val = getattr(plan, "intent", None)
    intent_str = str(intent_val).upper() if intent_val is not None else ""

    known_keywords = ("INDEX", "SCAN", "SUMMARIZE", "BATCH", "SYNC", "TRAVERSE", "IMPORT", "EXPORT")
    for kw in known_keywords:
        if kw in intent_str:
            return True

    params = getattr(plan, "parameters", None) or {}
    if isinstance(params, dict):
        if params.get("is_long_running") or params.get("long_running") or params.get("batch") or params.get("async_task") or params.get("background"):
            return True
        if params.get("job_type") in ("indexing", "scanning", "summarization", "batch", "sync"):
            return True

    target = getattr(plan, "target", None)
    if isinstance(target, str):
        target_lower = target.lower()
        if any(term in target_lower for term in ("workspace_index", "repo_scan", "batch_workflow", "large_document", "background_sync")):
            return True

    return False


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
        clarification_engine: ClarificationEngine | None = None,
        task_manager: LongRunningTaskManager | None = None,
        job_scheduler: BackgroundJobScheduler | None = None,
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
            clarification_engine: Optional injected ClarificationEngine.
            task_manager: Optional injected LongRunningTaskManager.
            job_scheduler: Optional injected BackgroundJobScheduler.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._validator = validator or ExecutionValidator(logger=self._logger)
        self._scheduler = scheduler or ExecutionScheduler(logger=self._logger)
        self._history = history or ExecutionHistory(logger=self._logger)
        self._matcher = CapabilityMatcher(logger=self._logger)
        self._recovery_engine = recovery_engine or RecoveryEngine(logger=self._logger)
        self._progress_monitor = progress_monitor or ProgressMonitor(logger=self._logger)
        self._state_manager = state_manager or ExecutionStateManager()
        self._decision_engine = decision_engine or DecisionEngine(clarification_engine=clarification_engine)
        self._failure_recovery_engine = failure_recovery_engine or FailureRecoveryEngine()
        self._clarification_engine = clarification_engine or ClarificationEngine()
        self._task_manager = task_manager or LongRunningTaskManager()
        self._job_scheduler = job_scheduler or BackgroundJobScheduler()

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
                pass

    @property
    def task_manager(self) -> LongRunningTaskManager:
        """Returns the injected or default LongRunningTaskManager."""
        return self._task_manager

    @property
    def job_scheduler(self) -> BackgroundJobScheduler:
        """Returns the injected or default BackgroundJobScheduler."""
        return self._job_scheduler



    def _safe_list_ready_scheduled_jobs(self, current_time: Any = None) -> list:
        try:
            return self._job_scheduler.list_ready_jobs(current_time=current_time) or []
        except Exception as e:
            self._logger.warning("Failed to list ready scheduled jobs", exc_info=e)
            return []

    def _safe_start_scheduled_job(self, job_id: str) -> bool:
        try:
            return self._job_scheduler.start_job_execution(job_id)
        except Exception as e:
            self._logger.warning("Failed to start scheduled job execution", extra={"job_id": job_id}, exc_info=e)
            return False

    def _safe_complete_scheduled_job(self, job_id: str, result_metadata: Any = None) -> bool:
        try:
            return self._job_scheduler.complete_job_execution(job_id, result_metadata=result_metadata)
        except Exception as e:
            self._logger.warning("Failed to complete scheduled job execution", extra={"job_id": job_id}, exc_info=e)
            return False

    def _safe_fail_scheduled_job(self, job_id: str, error_message: str) -> bool:
        try:
            return self._job_scheduler.fail_job_execution(job_id, error_message=error_message)
        except Exception as e:
            self._logger.warning("Failed to fail scheduled job execution", extra={"job_id": job_id}, exc_info=e)
            return False

    def execute_ready_scheduled_jobs(
        self,
        dispatcher: Any = None,
        current_time: Any = None,
    ) -> list:
        """Finds all ready background jobs, converts them to execution requests, and executes them.

        Args:
            dispatcher: Injected capability dispatcher.
            current_time: Optional reference datetime timestamp.

        Returns:
            List of execution response outputs.
        """
        ready_jobs = self._safe_list_ready_scheduled_jobs(current_time=current_time)
        results = []

        for job in ready_jobs:
            job_id = getattr(job, "job_id", None)
            if not job_id:
                continue

            request_payload = convert_to_execution_request(job)
            if not request_payload:
                continue

            self._safe_start_scheduled_job(job_id)
            self._logger.info("Scheduled Job Ready", extra={"job_id": job_id, "job_name": getattr(job, "name", "")})

            try:
                response = self.execute_plan(request_payload, dispatcher=dispatcher)
                results.append(response)

                is_success = getattr(response, "success", True) if response else True
                if is_success:
                    self._safe_complete_scheduled_job(job_id)
                else:
                    err_msg = getattr(response, "message", "Execution returned failure response")
                    self._safe_fail_scheduled_job(job_id, err_msg)
            except Exception as e:
                self._logger.warning("Error executing scheduled job", extra={"job_id": job_id}, exc_info=e)
                self._safe_fail_scheduled_job(job_id, str(e))

        return results



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

    def _safe_create_long_running_task(
        self,
        name: str,
        execution_id: str | None = None,
        total_steps: int = 0,
        metadata: dict | None = None,
    ) -> Any:
        try:
            task = self._task_manager.create_task(
                name=name,
                execution_id=execution_id,
                total_steps=total_steps,
                metadata=metadata or {},
            )
            self._logger.info("Long Running Task Detected", extra={"execution_id": execution_id, "task_name": name})
            if task:
                self._logger.info("Task Registered", extra={"execution_id": execution_id, "task_id": task.task_id})
            return task

        except Exception as e:
            self._logger.warning("Failed to create long-running task in task manager", exc_info=e)
            return None

    def _safe_queue_long_running_task(self, task_id: str) -> None:
        try:
            self._task_manager.queue_task(task_id)
            self._logger.info("Task Queued", extra={"task_id": task_id})
        except Exception as e:
            self._logger.warning("Failed to queue long-running task", exc_info=e)

    def _safe_start_long_running_task(self, task_id: str) -> None:
        try:
            self._task_manager.start_task(task_id)
            self._logger.info("Task Started", extra={"task_id": task_id})
        except Exception as e:
            self._logger.warning("Failed to start long-running task", exc_info=e)

    def _safe_update_long_running_task_progress(
        self,
        task_id: str,
        progress: float,
        current_step: int,
        total_steps: int,
    ) -> None:
        try:
            self._task_manager.update_progress(
                task_id=task_id,
                progress=progress,
                current_step=current_step,
                total_steps=total_steps,
            )
            self._logger.info("Task Progress Updated", extra={"task_id": task_id, "progress": progress})
        except Exception as e:
            self._logger.warning("Failed to update long-running task progress", exc_info=e)

    def _safe_complete_long_running_task(self, task_id: str, result_metadata: dict | None = None) -> None:
        try:
            self._task_manager.complete_task(task_id, result_metadata=result_metadata)
            self._logger.info("Task Completed", extra={"task_id": task_id})
        except Exception as e:
            self._logger.warning("Failed to complete long-running task", exc_info=e)

    def _safe_fail_long_running_task(self, task_id: str, error_message: str) -> None:
        try:
            self._task_manager.fail_task(task_id, error_message=error_message)
            self._logger.info("Task Failed", extra={"task_id": task_id, "error": error_message})
        except Exception as e:
            self._logger.warning("Failed to fail long-running task", exc_info=e)

    def _safe_cancel_long_running_task(self, task_id: str) -> None:
        try:
            self._task_manager.cancel_task(task_id)
            self._logger.info("Task Cancelled", extra={"task_id": task_id})
        except Exception as e:
            self._logger.warning("Failed to cancel long-running task", exc_info=e)


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

    def _safe_execute_recovery_plan(
        self,
        execution_id: str,
        step_id: str,
        step_plan: CoreExecutionPlan,
        dispatcher: Any,
        plan_parameters: dict,
        exception: Exception,
    ) -> bool:
        """Executes the recovery plan generated by FailureRecoveryEngine.
        Returns True if recovery succeeded and the step was successfully recovered/handled, False otherwise.
        """
        try:
            exec_state = self._state_manager.get_execution(execution_id)
            if not exec_state:
                return False

            retry_count = exec_state.retry_count
            context = RecoveryContext(
                execution_state=exec_state,
                execution_step=step_plan,
                resolved_preferences=plan_parameters.get("resolved_preferences") or plan_parameters,
                exception=exception,
                retry_count=retry_count,
            )

            # Build the recovery plan
            plan = self._failure_recovery_engine.build_recovery_plan(context)
            self._logger.info("Recovery Started", extra={"execution_id": execution_id, "strategy": plan.strategy.value})

            # Record recovery attempt on execution state
            exec_state.recovery_attempts += 1
            exec_state.last_recovery_strategy = plan.strategy.value
            exec_state._touch()

            if plan.strategy == RecoveryStrategy.RETRY:
                while exec_state.retry_count < plan.maximum_retry_count:
                    # Retry attempt logging
                    self._logger.info("Retry Attempt", extra={"execution_id": execution_id, "attempt": exec_state.retry_count + 1})
                    # Transitions status to RETRYING and increments the retry count in state manager
                    self._safe_mark_retrying(execution_id)
                    
                    # Dispatch again
                    try:
                        result = dispatcher.dispatch(step_plan)
                        if result.success:
                            self._logger.info("Recovery Successful", extra={"execution_id": execution_id})
                            exec_state.metadata["successful_recoveries"] = exec_state.metadata.get("successful_recoveries", 0) + 1
                            return True
                    except Exception as retry_err:
                        self._logger.error("Retry attempt threw exception", exc_info=retry_err)
                
                # If we exhausted retries
                self._logger.info("Recovery Failed", extra={"execution_id": execution_id})
                exec_state.metadata["failed_recoveries"] = exec_state.metadata.get("failed_recoveries", 0) + 1
                return False

            elif plan.strategy == RecoveryStrategy.WAIT:
                self._logger.info("Retry Attempt", extra={"execution_id": execution_id, "strategy": "WAIT"})
                # Wait using wait_seconds
                wait_time = plan.wait_seconds or 1.0
                import time
                time.sleep(wait_time)
                
                # Retry once after waiting
                self._safe_mark_retrying(execution_id)
                try:
                    result = dispatcher.dispatch(step_plan)
                    if result.success:
                        self._logger.info("Recovery Successful", extra={"execution_id": execution_id})
                        exec_state.metadata["successful_recoveries"] = exec_state.metadata.get("successful_recoveries", 0) + 1
                        return True
                except Exception as wait_err:
                    self._logger.error("Wait-retry attempt threw exception", exc_info=wait_err)

                self._logger.info("Recovery Failed", extra={"execution_id": execution_id})
                exec_state.metadata["failed_recoveries"] = exec_state.metadata.get("failed_recoveries", 0) + 1
                return False

            elif plan.strategy == RecoveryStrategy.USE_FALLBACK:
                self._logger.info("Fallback Applied", extra={"execution_id": execution_id, "fallback": plan.fallback_resource})
                if plan.fallback_resource:
                    step_plan.target = plan.fallback_resource
                    exec_state.metadata["fallback_usage"] = exec_state.metadata.get("fallback_usage", 0) + 1
                    
                    # Execute with fallback resource
                    try:
                        result = dispatcher.dispatch(step_plan)
                        if result.success:
                            self._logger.info("Recovery Successful", extra={"execution_id": execution_id})
                            exec_state.metadata["successful_recoveries"] = exec_state.metadata.get("successful_recoveries", 0) + 1
                            return True
                    except Exception as fallback_err:
                        self._logger.error("Fallback execution threw exception", exc_info=fallback_err)

                self._logger.info("Recovery Failed", extra={"execution_id": execution_id})
                exec_state.metadata["failed_recoveries"] = exec_state.metadata.get("failed_recoveries", 0) + 1
                return False

            elif plan.strategy == RecoveryStrategy.SKIP:
                self._logger.info("Skipped Step", extra={"execution_id": execution_id, "step_id": step_id})
                # Add step_id to skipped_steps on state
                exec_state.skipped_steps.append(step_id)
                exec_state._touch()
                self._logger.info("Recovery Successful", extra={"execution_id": execution_id})
                exec_state.metadata["successful_recoveries"] = exec_state.metadata.get("successful_recoveries", 0) + 1
                return True

            elif plan.strategy == RecoveryStrategy.ASK_USER:
                self._logger.info("Execution Waiting For Confirmation", extra={"execution_id": execution_id})
                # Mark as WAITING_FOR_CONFIRMATION
                self._state_manager.mark_waiting_for_confirmation(execution_id)
                return False

            elif plan.strategy == RecoveryStrategy.IGNORE:
                self._logger.info("Ignored Failure", extra={"execution_id": execution_id, "step_id": step_id})
                exec_state.ignored_failures.append(str(exception))
                exec_state._touch()
                self._logger.info("Recovery Successful", extra={"execution_id": execution_id})
                exec_state.metadata["successful_recoveries"] = exec_state.metadata.get("successful_recoveries", 0) + 1
                return True

            elif plan.strategy == RecoveryStrategy.ABORT:
                self._logger.info("Recovery Aborted", extra={"execution_id": execution_id})
                exec_state.metadata["failed_recoveries"] = exec_state.metadata.get("failed_recoveries", 0) + 1
                return False

            return False

        except Exception as e:
            self._logger.warning("Recovery failure fallback to original failure path", exc_info=e)
            return False

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
        # Determine execution_id and plan parameters
        plan_params = getattr(plan, "parameters", plan.get("parameters") if isinstance(plan, dict) else {}) or {}
        plan_intent = getattr(plan, "intent", plan.get("intent") if isinstance(plan, dict) else Intent.UNKNOWN)
        plan_target = getattr(plan, "target", plan.get("target") if isinstance(plan, dict) else None)

        execution_id = None
        if isinstance(plan_params, dict):
            execution_id = plan_params.get("execution_id")
            if not execution_id:
                metadata = plan_params.get("metadata")
                if isinstance(metadata, dict):
                    execution_id = metadata.get("execution_id")
            if not execution_id:
                req_metadata = plan_params.get("request_metadata")
                if isinstance(req_metadata, dict):
                    execution_id = req_metadata.get("execution_id")

        if not execution_id:
            try:
                raw_exec_id = getattr(plan, "execution_id", plan.get("execution_id") if isinstance(plan, dict) else None)
                execution_id = str(uuid.UUID(raw_exec_id))
            except Exception:
                execution_id = str(uuid.uuid4())

        intent_str = plan_intent.value if hasattr(plan_intent, "value") else str(plan_intent)
        self._logger.info("Starting execution session", extra={"execution_id": execution_id, "intent": intent_str})

        # Register execution and start running
        workflow_id = plan_target if plan_intent == Intent.RUN_WORKFLOW else None
        self._safe_create_execution(
            execution_id=execution_id,
            user_id=user_id,
            workflow_id=workflow_id,
            metadata=plan_params,

        )
        self._safe_mark_running(execution_id)

        # Detect and register Long-Running Task if applicable
        long_running_task = None
        if is_long_running_task(plan):
            intent_name = plan.intent.value if hasattr(plan.intent, "value") else str(plan.intent)
            task_name = f"{intent_name} - {plan.target or 'Task'}"
            total_plan_steps = len(plan.routes) if plan.routes else 0
            long_running_task = self._safe_create_long_running_task(
                name=task_name,
                execution_id=execution_id,
                total_steps=total_plan_steps,
                metadata=plan.parameters if isinstance(plan.parameters, dict) else {},
            )
            if long_running_task:
                self._safe_queue_long_running_task(long_running_task.task_id)
                self._safe_start_long_running_task(long_running_task.task_id)


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
            if long_running_task:
                self._safe_update_long_running_task_progress(
                    task_id=long_running_task.task_id,
                    progress=percentage,
                    current_step=i + 1,
                    total_steps=total_steps,
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
                if long_running_task:
                    self._safe_cancel_long_running_task(long_running_task.task_id)
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
                
                try:
                    from brain.execution.clarification_engine import ClarificationContext as ClarCtx
                    clar_metadata = {}
                    if exec_state and hasattr(exec_state, 'metadata') and exec_state.metadata:
                        clar_metadata.update(exec_state.metadata)
                    if plan.parameters:
                        clar_metadata.update(plan.parameters)
                    clar_context = ClarCtx(
                        assistant_context=decision_context.assistant_context if isinstance(decision_context.assistant_context, dict) else None,
                        execution_step=step_plan,
                        workspace_analysis=decision_context.workspace_analysis if isinstance(decision_context.workspace_analysis, dict) else None,
                        resolved_preferences=decision_context.resolved_preferences,
                        decision=decision,
                        metadata=clar_metadata,
                    )
                    req = self._clarification_engine.generate_request(clar_context)
                    if req:
                        self._logger.info("Clarification Requested", extra={"execution_id": execution_id})
                        self._logger.info("Execution Suspended", extra={"execution_id": execution_id})
                        self._logger.info("Awaiting User Confirmation", extra={"execution_id": execution_id})
                        
                        if exec_state:
                            from datetime import datetime, timezone
                            from .execution_state import ExecutionStatus as StateStatus
                            exec_state.waiting_for_confirmation = True
                            exec_state.clarification_request_id = req.clarification_id
                            exec_state.clarification_timestamp = datetime.now(timezone.utc)
                            exec_state.clarification_reason = decision.message
                            exec_state.status = StateStatus.WAITING_FOR_CONFIRMATION
                            exec_state._touch()
                        
                        overall_success = False
                        summary_error = f"User confirmation required: {decision.message}"
                        break
                    else:
                        self._logger.info("Clarification Not Required", extra={"execution_id": execution_id})
                        self._logger.info("Execution Resumed Ready", extra={"execution_id": execution_id})
                        self._safe_mark_paused(execution_id)
                        overall_success = False
                        summary_error = f"User confirmation required: {decision.message}"
                        break
                except Exception as e:
                    self._logger.warning("ClarificationEngine failed, continuing without blocking", exc_info=e)
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

                # Attempt autonomous recovery plan execution
                recovered = self._safe_execute_recovery_plan(
                    execution_id=execution_id,
                    step_id=step_id,
                    step_plan=step_plan,
                    dispatcher=dispatcher,
                    plan_parameters=plan.parameters,
                    exception=exc,
                )

                if recovered:
                    step_status = ExecutionStatus.SUCCESS
                    step_error = None
                    step_response = "Recovered via autonomous recovery strategy"
                    
                    record.status = ExecutionStatus.SUCCESS
                    record.response = step_response
                    record.error = None
                else:
                    state = self._state_manager.get_execution(execution_id)
                    from .execution_state import ExecutionStatus as StateStatus
                    if state and state.status == StateStatus.WAITING_FOR_CONFIRMATION:
                        overall_success = False
                        summary_error = f"Step '{step_id}' paused, waiting for user confirmation."
                        break
                    elif state and state.status == StateStatus.WAITING:
                        overall_success = False
                        summary_error = f"Step '{step_id}' paused, waiting."
                        break
                    else:
                        # Attempt legacy fallback recovery
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
            if long_running_task:
                self._safe_complete_long_running_task(
                    long_running_task.task_id,
                    result_metadata={"execution_id": execution_id},
                )
        elif long_running_task:
            exec_state = self._state_manager.get_execution(execution_id)
            status_str = str(getattr(exec_state, "status", ""))
            current_task = self._task_manager.get_task(long_running_task.task_id)
            task_status_str = str(getattr(current_task, "status", "")) if current_task else ""
            if current_task and "CANCELLED" not in task_status_str:
                if "CANCELLED" in status_str:
                    self._safe_cancel_long_running_task(long_running_task.task_id)
                else:
                    self._safe_fail_long_running_task(
                        long_running_task.task_id,
                        error_message=summary_error or "Execution failed",
                    )




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
