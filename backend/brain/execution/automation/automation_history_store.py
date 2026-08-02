"""Automation History Store for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Provides provider-independent storage and query capabilities for automation execution histories.
"""

from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional

from brain.execution.automation.interfaces import IAutomationHistory
from brain.execution.automation.automation_models import (
    AutomationExecution,
    AutomationHistory,
    AutomationStatus,
)


class AutomationHistoryStore(IAutomationHistory):
    """Thread-safe storage manager tracking execution history per automation rule."""

    def __init__(self) -> None:
        """Initializes AutomationHistoryStore."""
        self._lock = threading.RLock()
        self._history: Dict[str, List[AutomationExecution]] = {}

    def record_execution(self, execution: AutomationExecution) -> bool:
        """Record an AutomationExecution outcome.

        Args:
            execution: AutomationExecution model.

        Returns:
            True always.
        """
        with self._lock:
            if execution.rule_id not in self._history:
                self._history[execution.rule_id] = []

            self._history[execution.rule_id].append(execution)
            return True

    def get_history(self, rule_id: str) -> Optional[AutomationHistory]:
        """Fetch execution history summary for a rule_id.

        Args:
            rule_id: Rule identifier.

        Returns:
            AutomationHistory model or None if no executions recorded.
        """
        with self._lock:
            records = self._history.get(rule_id, [])
            if not records:
                return None

            total = len(records)
            successes = sum(1 for r in records if r.status == AutomationStatus.COMPLETED)
            failures = sum(1 for r in records if r.status == AutomationStatus.FAILED)
            last_run = records[-1].started_at if records else None

            return AutomationHistory(
                rule_id=rule_id,
                executions=list(records),
                total_runs=total,
                successful_runs=successes,
                failed_runs=failures,
                last_run=last_run,
                next_run=None,
                metadata={"recorded_count": len(records)},
            )

    def list_all_histories(self) -> List[AutomationHistory]:
        """List histories for all rules."""
        with self._lock:
            results: List[AutomationHistory] = []
            for r_id in self._history:
                h = self.get_history(r_id)
                if h:
                    results.append(h)
            return results

    def clear(self) -> None:
        """Clear all stored execution histories."""
        with self._lock:
            self._history.clear()
