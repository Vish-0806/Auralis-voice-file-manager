"""Assistant Memory Integration Runtime Coordinator for Auralis (Phase 13.5).

Manages runtime lifecycle, provider registration, health monitoring, statistics tracking,
and thread-safe operations using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.memory.assistant_memory_provider import AssistantMemoryProvider
from brain.assistant.memory.interfaces import (
    IAssistantMemoryProvider,
    IAssistantMemoryRuntime,
)
from brain.assistant.memory.models import (
    AssistantMemoryHealth,
    AssistantMemoryStatistics,
)

logger = logging.getLogger(__name__)


class AssistantMemoryRuntime(IAssistantMemoryRuntime):
    """Thread-safe runtime manager for assistant memory & context integration."""

    def __init__(self, provider: Optional[IAssistantMemoryProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._initialized = False
        self._start_time: Optional[float] = None

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    def get_provider(self) -> Optional[IAssistantMemoryProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IAssistantMemoryProvider) -> None:
        """Register an assistant memory provider instance thread-safely."""
        with self._lock:
            if not isinstance(provider, IAssistantMemoryProvider):
                raise TypeError("Provider must implement IAssistantMemoryProvider interface")
            self._provider = provider
            logger.debug("Registered assistant memory provider: %s", provider)

    def initialize(self) -> None:
        """Initialize the Assistant Memory Runtime."""
        with self._lock:
            if self._initialized:
                return

            if self._provider is None:
                self._provider = AssistantMemoryProvider()

            if not self._provider.is_initialized:
                self._provider.initialize()

            self._initialized = True
            self._start_time = time.time()
            logger.info("AssistantMemoryRuntime initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down the Assistant Memory Runtime."""
        with self._lock:
            if not self._initialized:
                return

            if self._provider is not None and self._provider.is_initialized:
                self._provider.shutdown()

            self._initialized = False
            self._start_time = None
            logger.info("AssistantMemoryRuntime shutdown complete")

    def clear(self) -> None:
        """Reset memory runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._initialized = False
            self._start_time = None

    def get_health(self) -> AssistantMemoryHealth:
        """Return aggregated health status."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self._initialized
            return AssistantMemoryHealth(
                status="READY" if healthy else "UNINITIALIZED",
                healthy=healthy,
                subsystems={"provider": False},
                statistics={},
                detected_issues=[] if healthy else ["No provider registered"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> AssistantMemoryStatistics:
        """Return performance and usage statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return AssistantMemoryStatistics(
                total_context_merges=0,
                total_snapshots_generated=0,
                preferences_merged=0,
                duplicates_removed=0,
                token_budget_trims=0,
                average_merge_latency_ms=0.0,
                uptime_seconds=uptime,
                metadata={},
            )
