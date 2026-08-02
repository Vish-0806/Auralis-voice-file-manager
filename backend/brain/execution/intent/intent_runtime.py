"""Intent Runtime for the Auralis Intent Resolution Subsystem (Phase 12.2).

Thread-safe singleton lifecycle manager orchestrating the IntentProvider.
Manages status transitions, process_intent delegation, health monitoring, and statistics.
"""

from enum import Enum
import logging
import threading
from typing import Optional

from brain.execution.intent.intent_models import (
    IntentContext,
    IntentHealth,
    IntentResolution,
    ResolutionStatistics,
)
from brain.execution.intent.intent_provider import IntentProvider
from brain.execution.intent.interfaces import IIntentRuntime

logger = logging.getLogger(__name__)


class IntentRuntimeStatus(str, Enum):
    """Lifecycle status states for the Intent Resolution Engine Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class IntentRuntime(IIntentRuntime):
    """Thread-safe singleton runtime managing the IntentProvider lifecycle."""

    def __init__(self, provider: Optional[IntentProvider] = None) -> None:
        """Initializes IntentRuntime with optional provider instance."""
        self._lock = threading.RLock()
        self._status = IntentRuntimeStatus.INITIALIZING
        self._provider = provider or IntentProvider()

    @property
    def status(self) -> IntentRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> IntentProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Intent Resolution Engine runtime.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == IntentRuntimeStatus.READY:
                return True

            try:
                self._status = IntentRuntimeStatus.READY
                logger.info("Intent Resolution Engine Runtime Initialized")
                return True
            except Exception as exc:
                self._status = IntentRuntimeStatus.ERROR
                logger.error("IntentRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down active intent resolution runtime.

        Returns:
            True always.
        """
        with self._lock:
            self._status = IntentRuntimeStatus.SHUTDOWN
            logger.info("Intent Resolution Engine Runtime Shutdown")
            return True

    def process_intent(
        self,
        text: str,
        context: Optional[IntentContext] = None,
    ) -> IntentResolution:
        """Process prompt text through the IntentProvider.

        Args:
            text: Raw input text prompt.
            context: Optional IntentContext object.

        Returns:
            Immutable IntentResolution model.
        """
        with self._lock:
            if self._status in (IntentRuntimeStatus.INITIALIZING, IntentRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = IntentRuntimeStatus.RUNNING

        try:
            return self._provider.resolve_intent(text, context=context)
        finally:
            with self._lock:
                if self._status == IntentRuntimeStatus.RUNNING:
                    self._status = prev_status if prev_status != IntentRuntimeStatus.INITIALIZING else IntentRuntimeStatus.READY

    def health_check(self) -> IntentHealth:
        """Fetch health check diagnostic status."""
        with self._lock:
            provider_health = self._provider.health_check()
            is_healthy = (self._status in (IntentRuntimeStatus.READY, IntentRuntimeStatus.RUNNING)) and provider_health.healthy

            issues = list(provider_health.detected_issues)
            if self._status == IntentRuntimeStatus.ERROR:
                issues.append("Runtime is in ERROR status")

            return IntentHealth(
                status=self._status.value if is_healthy else "ERROR",
                healthy=is_healthy,
                components=provider_health.components,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> ResolutionStatistics:
        """Fetch resolution statistics snapshot."""
        with self._lock:
            return self._provider.get_statistics()

    def clear(self) -> None:
        """Reset resolution statistics and transient state."""
        with self._lock:
            self._provider.clear()
            if self._status != IntentRuntimeStatus.SHUTDOWN:
                self._status = IntentRuntimeStatus.READY
            logger.info("IntentRuntime cleared")
