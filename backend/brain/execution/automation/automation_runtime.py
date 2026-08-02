"""Automation Runtime for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Thread-safe singleton lifecycle manager orchestrating the AutomationProvider.
Manages status transitions, rule registration, trigger execution, health monitoring, and statistics.
"""

from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.execution.automation.interfaces import IAutomationRuntime
from brain.execution.automation.automation_models import (
    AutomationExecution,
    AutomationHealth,
    AutomationHistory,
    AutomationRule,
    AutomationStatistics,
)
from brain.execution.automation.automation_provider import AutomationProvider

logger = logging.getLogger(__name__)


class AutomationRuntimeStatus(str, Enum):
    """Lifecycle status states for the Automation & Scheduling Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class AutomationRuntime(IAutomationRuntime):
    """Thread-safe singleton runtime managing the AutomationProvider lifecycle."""

    def __init__(self, provider: Optional[AutomationProvider] = None) -> None:
        """Initializes AutomationRuntime with optional provider instance."""
        self._lock = threading.RLock()
        self._status = AutomationRuntimeStatus.INITIALIZING
        self._provider = provider or AutomationProvider()

    @property
    def status(self) -> AutomationRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> AutomationProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Automation & Scheduling Runtime.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == AutomationRuntimeStatus.READY:
                return True

            try:
                self._status = AutomationRuntimeStatus.READY
                logger.info("Automation & Scheduling Runtime Initialized")
                return True
            except Exception as exc:
                self._status = AutomationRuntimeStatus.ERROR
                logger.error("AutomationRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down automation runtime.

        Returns:
            True always.
        """
        with self._lock:
            self._status = AutomationRuntimeStatus.SHUTDOWN
            logger.info("Automation & Scheduling Runtime Shutdown")
            return True

    def register_rule(self, rule: AutomationRule) -> bool:
        """Register automation rule through provider."""
        with self._lock:
            if self._status in (AutomationRuntimeStatus.INITIALIZING, AutomationRuntimeStatus.SHUTDOWN):
                self.initialize()
        return self._provider.register_rule(rule)

    def trigger_manually(
        self,
        rule_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AutomationExecution:
        """Trigger automation rule manually through provider."""
        with self._lock:
            if self._status in (AutomationRuntimeStatus.INITIALIZING, AutomationRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = AutomationRuntimeStatus.RUNNING

        try:
            return self._provider.trigger_manually(rule_id, context=context)
        finally:
            with self._lock:
                if self._status == AutomationRuntimeStatus.RUNNING:
                    self._status = prev_status if prev_status != AutomationRuntimeStatus.INITIALIZING else AutomationRuntimeStatus.READY

    def evaluate_and_execute(
        self,
        event_context: Optional[Dict[str, Any]] = None,
    ) -> List[AutomationExecution]:
        """Evaluate active rules and execute due rules."""
        with self._lock:
            if self._status in (AutomationRuntimeStatus.INITIALIZING, AutomationRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = AutomationRuntimeStatus.RUNNING

        try:
            return self._provider.evaluate_and_execute(event_context=event_context)
        finally:
            with self._lock:
                if self._status == AutomationRuntimeStatus.RUNNING:
                    self._status = prev_status if prev_status != AutomationRuntimeStatus.INITIALIZING else AutomationRuntimeStatus.READY

    def get_history(self, rule_id: str) -> Optional[AutomationHistory]:
        """Fetch history for rule_id."""
        return self._provider.get_history(rule_id)

    def health_check(self) -> AutomationHealth:
        """Fetch health check diagnostic status."""
        with self._lock:
            provider_health = self._provider.health_check()
            is_healthy = (self._status in (AutomationRuntimeStatus.READY, AutomationRuntimeStatus.RUNNING)) and provider_health.healthy

            issues = list(provider_health.detected_issues)
            if self._status == AutomationRuntimeStatus.ERROR:
                issues.append("Automation runtime is in ERROR status")

            return AutomationHealth(
                status=self._status.value if is_healthy else "ERROR",
                healthy=is_healthy,
                components=provider_health.components,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> AutomationStatistics:
        """Fetch automation execution statistics snapshot."""
        with self._lock:
            return self._provider.get_statistics()

    def clear(self) -> None:
        """Reset automation statistics and transient state."""
        with self._lock:
            self._provider.clear()
            if self._status != AutomationRuntimeStatus.SHUTDOWN:
                self._status = AutomationRuntimeStatus.READY
            logger.info("AutomationRuntime cleared")
