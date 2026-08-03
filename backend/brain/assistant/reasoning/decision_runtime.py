"""Decision Runtime Coordinator for Auralis (Phase 13.4).

Manages decision coordinator runtime lifecycle, provider registration, health monitoring,
statistics tracking, and thread-safe operations using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.reasoning.decision_provider import DecisionProvider
from brain.assistant.reasoning.interfaces import (
    IDecisionProvider,
    IDecisionRuntime,
)
from brain.assistant.reasoning.models import (
    DecisionHealth,
    DecisionStatistics,
)

logger = logging.getLogger(__name__)


class DecisionRuntime(IDecisionRuntime):
    """Thread-safe runtime coordinator for decision routing and reasoning evaluation."""

    def __init__(self, provider: Optional[IDecisionProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._initialized = False
        self._start_time: Optional[float] = None

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    def get_provider(self) -> Optional[IDecisionProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IDecisionProvider) -> None:
        """Register a decision provider instance thread-safely."""
        with self._lock:
            if not isinstance(provider, IDecisionProvider):
                raise TypeError("Provider must implement IDecisionProvider interface")
            self._provider = provider
            logger.debug("Registered decision provider: %s", provider)

    def initialize(self) -> None:
        """Initialize the Decision Runtime."""
        with self._lock:
            if self._initialized:
                return

            if self._provider is None:
                self._provider = DecisionProvider()

            if not self._provider.is_initialized:
                self._provider.initialize()

            self._initialized = True
            self._start_time = time.time()
            logger.info("DecisionRuntime initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down the Decision Runtime."""
        with self._lock:
            if not self._initialized:
                return

            if self._provider is not None and self._provider.is_initialized:
                self._provider.shutdown()

            self._initialized = False
            self._start_time = None
            logger.info("DecisionRuntime shutdown complete")

    def clear(self) -> None:
        """Reset decision runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._initialized = False
            self._start_time = None

    def get_health(self) -> DecisionHealth:
        """Return aggregated health status."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self._initialized
            return DecisionHealth(
                status="READY" if healthy else "UNINITIALIZED",
                healthy=healthy,
                subsystems={"provider": False},
                statistics={},
                detected_issues=[] if healthy else ["No provider registered"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> DecisionStatistics:
        """Return performance and usage statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return DecisionStatistics(
                total_requests_evaluated=0,
                direct_executions_routed=0,
                ai_required_routed=0,
                planner_required_routed=0,
                clarifications_routed=0,
                confirmations_routed=0,
                rejections_routed=0,
                average_evaluation_latency_ms=0.0,
                uptime_seconds=uptime,
                metadata={},
            )
