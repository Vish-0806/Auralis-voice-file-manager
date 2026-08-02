"""Abstract Base Class interfaces for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Defines canonical interfaces for scheduler, trigger engine, executor, history store, provider, and runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.execution.automation.automation_models import (
    AutomationExecution,
    AutomationHealth,
    AutomationHistory,
    AutomationRule,
    AutomationStatistics,
    AutomationTrigger,
)


class IAutomationScheduler(ABC):
    """Interface for registering rules, scheduling one-time/recurring/cron events, and calculating next runs."""

    @abstractmethod
    def register_rule(self, rule: AutomationRule) -> bool:
        """Register automation rule in scheduler."""
        pass

    @abstractmethod
    def unregister_rule(self, rule_id: str) -> bool:
        """Unregister automation rule from scheduler."""
        pass

    @abstractmethod
    def get_due_rules(self) -> List[AutomationRule]:
        """Fetch active rules that are due for execution."""
        pass


class IAutomationTriggerEngine(ABC):
    """Interface for evaluating time, manual, system event, and task completion triggers."""

    @abstractmethod
    def evaluate_trigger(self, trigger: AutomationTrigger, event_context: Optional[Dict[str, Any]] = None) -> bool:
        """Evaluate whether a trigger conditions match current event context."""
        pass


class IAutomationExecutor(ABC):
    """Interface for dispatching automation rule execution to Task Runtime, Workflow Engine, or Orchestrator."""

    @abstractmethod
    def execute_rule(self, rule: AutomationRule, context: Optional[Dict[str, Any]] = None) -> AutomationExecution:
        """Execute action payload for an automation rule."""
        pass


class IAutomationHistory(ABC):
    """Interface for storing and querying automation execution histories."""

    @abstractmethod
    def record_execution(self, execution: AutomationExecution) -> bool:
        """Record execution outcome for a rule."""
        pass

    @abstractmethod
    def get_history(self, rule_id: str) -> Optional[AutomationHistory]:
        """Fetch execution history for a rule."""
        pass


class IAutomationProvider(ABC):
    """Interface for aggregate Automation Provider."""

    @abstractmethod
    def register_rule(self, rule: AutomationRule) -> bool:
        """Register automation rule."""
        pass

    @abstractmethod
    def trigger_manually(self, rule_id: str, context: Optional[Dict[str, Any]] = None) -> AutomationExecution:
        """Manually trigger an automation rule."""
        pass

    @abstractmethod
    def evaluate_and_execute(self, event_context: Optional[Dict[str, Any]] = None) -> List[AutomationExecution]:
        """Evaluate all active rules and execute due rules."""
        pass

    @abstractmethod
    def health_check(self) -> AutomationHealth:
        """Report component health statuses."""
        pass

    @abstractmethod
    def get_statistics(self) -> AutomationStatistics:
        """Return snapshot of aggregated automation statistics."""
        pass


class IAutomationRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize automation runtime lifecycle."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down automation runtime lifecycle."""
        pass

    @abstractmethod
    def register_rule(self, rule: AutomationRule) -> bool:
        """Register automation rule through provider."""
        pass

    @abstractmethod
    def trigger_manually(self, rule_id: str, context: Optional[Dict[str, Any]] = None) -> AutomationExecution:
        """Trigger rule manually through provider."""
        pass

    @abstractmethod
    def health_check(self) -> AutomationHealth:
        """Fetch real-time health diagnostic status."""
        pass

    @abstractmethod
    def get_statistics(self) -> AutomationStatistics:
        """Fetch snapshot of automation execution statistics."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset automation statistics and transient state."""
        pass
