"""Assistant Integration Runtime Coordinator for Auralis (Phase 13.9).

Manages integration gateway runtime lifecycle, provider registration, restart mechanics,
health monitoring, statistics tracking, and thread-safe operations using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.integration.assistant_integration_provider import AssistantIntegrationProvider
from brain.assistant.integration.interfaces import (
    IAssistantIntegrationProvider,
    IAssistantIntegrationRuntime,
)
from brain.assistant.integration.models import (
    AssistantIntegrationCapabilities,
    AssistantIntegrationHealth,
    AssistantIntegrationStatistics,
)

logger = logging.getLogger(__name__)


class AssistantIntegrationRuntime(IAssistantIntegrationRuntime):
    """Thread-safe top-level runtime coordinator for the Assistant Integration Gateway."""

    def __init__(self, provider: Optional[IAssistantIntegrationProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._initialized = False
        self._start_time: Optional[float] = None

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    def get_provider(self) -> Optional[IAssistantIntegrationProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IAssistantIntegrationProvider) -> None:
        """Register an integration provider instance thread-safely."""
        with self._lock:
            if not isinstance(provider, IAssistantIntegrationProvider):
                raise TypeError("Provider must implement IAssistantIntegrationProvider interface")
            self._provider = provider
            logger.debug("Registered integration provider: %s", provider)

    def initialize(self) -> None:
        """Initialize the Assistant Integration Runtime."""
        with self._lock:
            if self._initialized:
                return

            if self._provider is None:
                self._provider = AssistantIntegrationProvider()

            if not self._provider.is_initialized:
                self._provider.initialize()

            self._initialized = True
            self._start_time = time.time()
            logger.info("AssistantIntegrationRuntime initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down the Assistant Integration Runtime."""
        with self._lock:
            if not self._initialized:
                return

            if self._provider is not None and self._provider.is_initialized:
                self._provider.shutdown()

            self._initialized = False
            self._start_time = None
            logger.info("AssistantIntegrationRuntime shutdown complete")

    def restart(self) -> None:
        """Restart the Assistant Integration Runtime thread-safely."""
        with self._lock:
            logger.info("Restarting AssistantIntegrationRuntime...")
            self.shutdown()
            self.clear()
            self.initialize()
            logger.info("AssistantIntegrationRuntime restart complete")

    def clear(self) -> None:
        """Reset integration runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._initialized = False
            self._start_time = None

    def get_health(self) -> AssistantIntegrationHealth:
        """Return aggregated health status across all 12 runtimes."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self._initialized
            return AssistantIntegrationHealth(
                status="READY" if healthy else "UNINITIALIZED",
                healthy=healthy,
                availability_percentage=100.0 if healthy else 0.0,
                subsystem_health={},
                detected_issues=[] if healthy else ["No provider registered"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> AssistantIntegrationStatistics:
        """Return performance and usage statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return AssistantIntegrationStatistics(
                total_requests_handled=0,
                successful_requests=0,
                failed_requests=0,
                pipeline_executions=0,
                average_pipeline_latency_ms=0.0,
                registered_runtimes_count=0,
                uptime_seconds=uptime,
                metadata={},
            )

    def get_capabilities(self) -> AssistantIntegrationCapabilities:
        """Return aggregated integration capabilities specifications."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_capabilities()
            return AssistantIntegrationCapabilities()
