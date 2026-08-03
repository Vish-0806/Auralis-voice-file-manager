"""Proactive Runtime Coordinator for Auralis (Phase 13.8).

Manages proactive behavior runtime lifecycle, provider registration, restart mechanics,
health monitoring, statistics tracking, and thread-safe operations using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.proactive.interfaces import (
    IProactiveProvider,
    IProactiveRuntime,
)
from brain.assistant.proactive.models import (
    ProactiveCapabilities,
    ProactiveHealth,
    ProactiveStatistics,
)
from brain.assistant.proactive.proactive_provider import ProactiveProvider

logger = logging.getLogger(__name__)


class ProactiveRuntime(IProactiveRuntime):
    """Thread-safe top-level runtime coordinator for Proactive Assistant & Notifications."""

    def __init__(self, provider: Optional[IProactiveProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._initialized = False
        self._start_time: Optional[float] = None

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    def get_provider(self) -> Optional[IProactiveProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IProactiveProvider) -> None:
        """Register a proactive provider instance thread-safely."""
        with self._lock:
            if not isinstance(provider, IProactiveProvider):
                raise TypeError("Provider must implement IProactiveProvider interface")
            self._provider = provider
            logger.debug("Registered proactive provider: %s", provider)

    def initialize(self) -> None:
        """Initialize the Proactive Runtime."""
        with self._lock:
            if self._initialized:
                return

            if self._provider is None:
                self._provider = ProactiveProvider()

            if not self._provider.is_initialized:
                self._provider.initialize()

            self._initialized = True
            self._start_time = time.time()
            logger.info("ProactiveRuntime initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down the Proactive Runtime."""
        with self._lock:
            if not self._initialized:
                return

            if self._provider is not None and self._provider.is_initialized:
                self._provider.shutdown()

            self._initialized = False
            self._start_time = None
            logger.info("ProactiveRuntime shutdown complete")

    def restart(self) -> None:
        """Restart the Proactive Runtime thread-safely."""
        with self._lock:
            logger.info("Restarting ProactiveRuntime...")
            self.shutdown()
            self.clear()
            self.initialize()
            logger.info("ProactiveRuntime restart complete")

    def clear(self) -> None:
        """Reset proactive runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._initialized = False
            self._start_time = None

    def get_health(self) -> ProactiveHealth:
        """Return aggregated health status."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self._initialized
            return ProactiveHealth(
                status="READY" if healthy else "UNINITIALIZED",
                healthy=healthy,
                subsystems={"provider": False},
                statistics={},
                detected_issues=[] if healthy else ["No provider registered"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> ProactiveStatistics:
        """Return performance and usage statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return ProactiveStatistics(
                total_evaluations=0,
                total_recommendations_generated=0,
                total_notifications_created=0,
                notifications_dismissed=0,
                notifications_archived=0,
                duplicates_suppressed=0,
                cooldowns_enforced=0,
                average_evaluation_latency_ms=0.0,
                uptime_seconds=uptime,
                metadata={},
            )

    def get_capabilities(self) -> ProactiveCapabilities:
        """Return proactive capabilities specifications."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_capabilities()
            return ProactiveCapabilities()
