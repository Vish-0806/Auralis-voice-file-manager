"""Response Runtime Coordinator for Auralis (Phase 13.6).

Manages runtime lifecycle, provider registration, health monitoring, statistics tracking,
and thread-safe operations using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.response.interfaces import (
    IResponseProvider,
    IResponseRuntime,
)
from brain.assistant.response.models import (
    ResponseHealth,
    ResponseStatistics,
)
from brain.assistant.response.response_provider import ResponseProvider

logger = logging.getLogger(__name__)


class ResponseRuntime(IResponseRuntime):
    """Thread-safe runtime coordinator for assistant response generation and streaming."""

    def __init__(self, provider: Optional[IResponseProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._initialized = False
        self._start_time: Optional[float] = None

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    def get_provider(self) -> Optional[IResponseProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IResponseProvider) -> None:
        """Register a response provider instance thread-safely."""
        with self._lock:
            if not isinstance(provider, IResponseProvider):
                raise TypeError("Provider must implement IResponseProvider interface")
            self._provider = provider
            logger.debug("Registered response provider: %s", provider)

    def initialize(self) -> None:
        """Initialize the Response Runtime."""
        with self._lock:
            if self._initialized:
                return

            if self._provider is None:
                self._provider = ResponseProvider()

            if not self._provider.is_initialized:
                self._provider.initialize()

            self._initialized = True
            self._start_time = time.time()
            logger.info("ResponseRuntime initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down the Response Runtime."""
        with self._lock:
            if not self._initialized:
                return

            if self._provider is not None and self._provider.is_initialized:
                self._provider.shutdown()

            self._initialized = False
            self._start_time = None
            logger.info("ResponseRuntime shutdown complete")

    def clear(self) -> None:
        """Reset response runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._initialized = False
            self._start_time = None

    def get_health(self) -> ResponseHealth:
        """Return aggregated health status."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self._initialized
            return ResponseHealth(
                status="READY" if healthy else "UNINITIALIZED",
                healthy=healthy,
                subsystems={"provider": False},
                statistics={},
                detected_issues=[] if healthy else ["No provider registered"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> ResponseStatistics:
        """Return performance and usage statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return ResponseStatistics(
                total_responses_built=0,
                total_streams_generated=0,
                total_chunks_emitted=0,
                average_response_latency_ms=0.0,
                formats_rendered={},
                uptime_seconds=uptime,
                metadata={},
            )
