"""Automation Scheduler for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Responsible for rule registration, interval calculation, cron-style scheduling abstraction,
and due rule identification. Does not contain rule execution logic.
"""

from datetime import datetime, timedelta, timezone
import threading
from typing import Dict, List, Optional

from brain.execution.automation.interfaces import IAutomationScheduler
from brain.execution.automation.automation_models import (
    AutomationRule,
    AutomationScheduleType,
    AutomationTriggerType,
)


class AutomationScheduler(IAutomationScheduler):
    """Thread-safe rule scheduler storing rules and calculating next run schedules."""

    def __init__(self) -> None:
        """Initializes AutomationScheduler with thread-safe storage."""
        self._lock = threading.RLock()
        self._rules: Dict[str, AutomationRule] = {}
        self._last_runs: Dict[str, datetime] = {}

    def register_rule(self, rule: AutomationRule) -> bool:
        """Register an AutomationRule.

        Args:
            rule: AutomationRule model.

        Returns:
            True if registered successfully.
        """
        with self._lock:
            self._rules[rule.rule_id] = rule
            return True

    def unregister_rule(self, rule_id: str) -> bool:
        """Unregister an AutomationRule by rule_id.

        Args:
            rule_id: Rule identifier.

        Returns:
            True if removed, False if not found.
        """
        with self._lock:
            if rule_id in self._rules:
                self._rules.pop(rule_id)
                self._last_runs.pop(rule_id, None)
                return True
            return False

    def mark_run(self, rule_id: str, run_time: Optional[datetime] = None) -> None:
        """Record the last execution timestamp for a rule."""
        with self._lock:
            self._last_runs[rule_id] = run_time or datetime.now(timezone.utc)

    def calculate_next_run(self, rule: AutomationRule) -> Optional[datetime]:
        """Calculate the next execution timestamp for an automation rule.

        Args:
            rule: AutomationRule model.

        Returns:
            Datetime object of next run or None if not scheduled.
        """
        if not rule.enabled or not rule.trigger.schedule:
            return None

        sched = rule.trigger.schedule
        last_r = self._last_runs.get(rule.rule_id)

        if sched.schedule_type == AutomationScheduleType.ONE_TIME:
            if last_r is not None:
                return None  # Already ran
            return sched.start_time or datetime.now(timezone.utc)

        elif sched.schedule_type == AutomationScheduleType.RECURRING:
            interval = sched.interval_seconds or 60.0
            if last_r is None:
                base_time = sched.start_time or datetime.now(timezone.utc)
                return base_time
            return last_r + timedelta(seconds=interval)

        elif sched.schedule_type == AutomationScheduleType.CRON:
            # Simple cron-style abstraction: default interval fallback if cron expression specified
            interval = 300.0  # Default 5-minute interval for cron abstraction
            if sched.interval_seconds:
                interval = sched.interval_seconds
            if last_r is None:
                return datetime.now(timezone.utc)
            return last_r + timedelta(seconds=interval)

        return None

    def get_due_rules(self) -> List[AutomationRule]:
        """Fetch active rules whose schedule criteria are due for execution.

        Returns:
            List of due AutomationRule objects.
        """
        now = datetime.now(timezone.utc)
        due: List[AutomationRule] = []

        with self._lock:
            for rule_id, rule in self._rules.items():
                if not rule.enabled:
                    continue

                if rule.trigger.trigger_type == AutomationTriggerType.TIME:
                    next_r = self.calculate_next_run(rule)
                    if next_r and now >= next_r:
                        due.append(rule)

        return due

    def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        """Fetch rule by rule_id."""
        with self._lock:
            return self._rules.get(rule_id)

    def list_rules(self) -> List[AutomationRule]:
        """List all registered rules."""
        with self._lock:
            return list(self._rules.values())

    def clear(self) -> None:
        """Clear all registered rules."""
        with self._lock:
            self._rules.clear()
            self._last_runs.clear()
