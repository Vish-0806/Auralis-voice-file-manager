"""Automation Executor for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Executes automation rule action payloads by dispatching to Task Runtime, Workflow Execution Engine,
or Command Execution Orchestrator according to execution mode.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, Optional, Set

from brain.execution.automation.interfaces import IAutomationExecutor
from brain.execution.automation.automation_models import (
    AutomationExecution,
    AutomationExecutionMode,
    AutomationRule,
    AutomationStatus,
)

logger = logging.getLogger(__name__)


class AutomationExecutor(IAutomationExecutor):
    """Executor dispatching rule payloads to Task, Workflow, or Command Orchestrator runtimes."""

    def __init__(
        self,
        task_runtime: Optional[Any] = None,
        workflow_runtime: Optional[Any] = None,
        command_orchestrator: Optional[Any] = None,
    ) -> None:
        """Initializes AutomationExecutor with optional injected subsystem runtimes."""
        self._lock = threading.RLock()
        self._task_runtime = task_runtime
        self._workflow_runtime = workflow_runtime
        self._command_orchestrator = command_orchestrator

        self._paused_rules: Set[str] = set()
        self._cancelled_rules: Set[str] = set()

    def execute_rule(
        self,
        rule: AutomationRule,
        context: Optional[Dict[str, Any]] = None,
    ) -> AutomationExecution:
        """Execute action payload for an AutomationRule.

        Args:
            rule: AutomationRule object.
            context: Optional contextual parameters.

        Returns:
            AutomationExecution model.
        """
        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)

        with self._lock:
            if rule.rule_id in self._cancelled_rules:
                return AutomationExecution(
                    rule_id=rule.rule_id,
                    status=AutomationStatus.CANCELLED,
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                    duration_seconds=0.0,
                    error="Rule execution cancelled before dispatch",
                )

        output: Dict[str, Any] = {}
        error_msg: Optional[str] = None
        final_status = AutomationStatus.COMPLETED

        try:
            payload = rule.action_payload
            mode = rule.mode

            if mode == AutomationExecutionMode.TASK_MANAGED and self._task_runtime and hasattr(self._task_runtime, "process_task"):
                t_res = self._task_runtime.process_task(payload, context=context)
                output = {"task_status": getattr(t_res, "status", "COMPLETED"), "task_id": getattr(t_res, "task_id", "")}

            elif mode == AutomationExecutionMode.WORKFLOW_MANAGED and self._workflow_runtime and hasattr(self._workflow_runtime, "process_workflow"):
                wf_res = self._workflow_runtime.process_workflow(payload, context=context)
                output = {"workflow_status": getattr(wf_res, "status", "COMPLETED"), "workflow_id": getattr(wf_res, "workflow_id", "")}

            elif mode == AutomationExecutionMode.ORCHESTRATED and self._command_orchestrator and hasattr(self._command_orchestrator, "orchestrate"):
                prompt = str(payload) if payload else rule.name
                orch_res = self._command_orchestrator.orchestrate(prompt, context=context)
                output = dict(getattr(orch_res, "output", {}))

            else:
                # Independent execution fallback
                output = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "result": f"Executed action '{payload}'",
                }

        except Exception as exc:
            final_status = AutomationStatus.FAILED
            error_msg = str(exc)
            logger.error("Automation rule '%s' execution failed: %s", rule.rule_id, exc)

        elapsed_sec = round(time.perf_counter() - start_time, 3)

        return AutomationExecution(
            rule_id=rule.rule_id,
            status=final_status,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            duration_seconds=elapsed_sec,
            output=output,
            error=error_msg,
            metadata={"execution_mode": rule.mode.value},
        )

    def pause_rule(self, rule_id: str) -> bool:
        """Pause execution for a rule."""
        with self._lock:
            self._paused_rules.add(rule_id)
            return True

    def resume_rule(self, rule_id: str) -> bool:
        """Resume execution for a rule."""
        with self._lock:
            if rule_id in self._paused_rules:
                self._paused_rules.remove(rule_id)
                return True
            return False

    def cancel_rule(self, rule_id: str) -> bool:
        """Cancel execution for a rule."""
        with self._lock:
            self._cancelled_rules.add(rule_id)
            return True
