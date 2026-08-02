"""Automation Provider for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Aggregates Scheduler, TriggerEngine, Executor, and HistoryStore into a unified, thread-safe provider.
Supports rule registration, manual triggers, event evaluation, health monitoring, and statistics.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.execution.automation.interfaces import (
    IAutomationExecutor,
    IAutomationHistory,
    IAutomationProvider,
    IAutomationScheduler,
    IAutomationTriggerEngine,
)
from brain.execution.automation.automation_executor import AutomationExecutor
from brain.execution.automation.automation_history_store import AutomationHistoryStore
from brain.execution.automation.automation_models import (
    AutomationExecution,
    AutomationHealth,
    AutomationHistory,
    AutomationRule,
    AutomationStatistics,
    AutomationStatus,
    AutomationTriggerType,
)
from brain.execution.automation.automation_scheduler import AutomationScheduler
from brain.execution.automation.automation_trigger_engine import AutomationTriggerEngine

logger = logging.getLogger(__name__)


class AutomationProvider(IAutomationProvider):
    """Thread-safe provider aggregating automation scheduler, trigger engine, executor, and history store."""

    def __init__(
        self,
        scheduler: Optional[IAutomationScheduler] = None,
        trigger_engine: Optional[IAutomationTriggerEngine] = None,
        executor: Optional[IAutomationExecutor] = None,
        history_store: Optional[IAutomationHistory] = None,
    ) -> None:
        """Initializes AutomationProvider with injected or default components."""
        self._lock = threading.RLock()
        self._scheduler = scheduler or AutomationScheduler()
        self._trigger_engine = trigger_engine or AutomationTriggerEngine()
        self._executor = executor or AutomationExecutor()
        self._history_store = history_store or AutomationHistoryStore()

        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        self._total_duration_seconds = 0.0

    def register_rule(self, rule: AutomationRule) -> bool:
        """Register an automation rule."""
        return self._scheduler.register_rule(rule)

    def trigger_manually(
        self,
        rule_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AutomationExecution:
        """Manually trigger an automation rule by rule_id.

        Args:
            rule_id: Rule identifier.
            context: Optional contextual parameters.

        Returns:
            AutomationExecution model.
        """
        start_time = time.perf_counter()
        rule = getattr(self._scheduler, "get_rule", lambda r: None)(rule_id)
        if not rule:
            execution = AutomationExecution(
                rule_id=rule_id,
                status=AutomationStatus.FAILED,
                error=f"Automation rule '{rule_id}' not found",
            )
            self._record_outcome(execution, 0.0)
            return execution

        execution = self._executor.execute_rule(rule, context=context)
        elapsed = time.perf_counter() - start_time
        self._record_outcome(execution, elapsed)
        if hasattr(self._scheduler, "mark_run"):
            self._scheduler.mark_run(rule_id)

        return execution

    def evaluate_and_execute(
        self,
        event_context: Optional[Dict[str, Any]] = None,
    ) -> List[AutomationExecution]:
        """Evaluate active rules and execute due rules.

        Args:
            event_context: Event context dictionary.

        Returns:
            List of AutomationExecution records.
        """
        results: List[AutomationExecution] = []
        due_rules = self._scheduler.get_due_rules()

        for rule in due_rules:
            if self._trigger_engine.evaluate_trigger(rule.trigger, event_context=event_context):
                start_time = time.perf_counter()
                execution = self._executor.execute_rule(rule, context=event_context)
                elapsed = time.perf_counter() - start_time

                self._record_outcome(execution, elapsed)
                if hasattr(self._scheduler, "mark_run"):
                    self._scheduler.mark_run(rule.rule_id)
                results.append(execution)

        return results

    def get_history(self, rule_id: str) -> Optional[AutomationHistory]:
        """Fetch history for rule_id."""
        return self._history_store.get_history(rule_id)

    def health_check(self) -> AutomationHealth:
        """Report component health statuses."""
        with self._lock:
            registered = {
                "AutomationScheduler": self._scheduler is not None,
                "AutomationTriggerEngine": self._trigger_engine is not None,
                "AutomationExecutor": self._executor is not None,
                "AutomationHistoryStore": self._history_store is not None,
            }
            all_ok = all(registered.values())

            return AutomationHealth(
                status="READY" if all_ok else "ERROR",
                healthy=all_ok,
                components=registered,
                statistics=self.get_statistics().model_dump(),
                detected_issues=[] if all_ok else ["One or more automation sub-components are unavailable"],
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> AutomationStatistics:
        """Return snapshot of aggregated automation statistics."""
        with self._lock:
            rules_list = getattr(self._scheduler, "list_rules", lambda: [])()
            total_rules = len(rules_list)
            active_rules = sum(1 for r in rules_list if getattr(r, "enabled", True))
            avg_duration = (self._total_duration_seconds / self._total_executions) if self._total_executions > 0 else 0.0

            return AutomationStatistics(
                total_rules=total_rules,
                active_rules=active_rules,
                total_executions=self._total_executions,
                successful_executions=self._successful_executions,
                failed_executions=self._failed_executions,
                average_duration_seconds=round(avg_duration, 3),
                metadata={"thread_safety": "PROTECTED"},
            )

    def clear(self) -> None:
        """Reset automation statistics and history store."""
        with self._lock:
            self._total_executions = 0
            self._successful_executions = 0
            self._failed_executions = 0
            self._total_duration_seconds = 0.0
            if hasattr(self._scheduler, "clear"):
                self._scheduler.clear()
            if hasattr(self._history_store, "clear"):
                self._history_store.clear()

    def _record_outcome(self, execution: AutomationExecution, duration_sec: float) -> None:
        """Internal helper recording execution outcome in statistics and history store."""
        with self._lock:
            self._total_executions += 1
            if execution.status == AutomationStatus.COMPLETED:
                self._successful_executions += 1
            else:
                self._failed_executions += 1
            self._total_duration_seconds += duration_sec

        self._history_store.record_execution(execution)
