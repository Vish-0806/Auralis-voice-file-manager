"""Dialogue Runtime Coordinator for Auralis (Phase 13.3).

Manages dialogue subsystem lifecycle, provider registration, health monitoring, statistics,
and thread-safe operations using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.dialogue.dialogue_provider import DialogueProvider
from brain.assistant.dialogue.interfaces import (
    IDialogueProvider,
    IDialogueRuntime,
)
from brain.assistant.dialogue.models import (
    DialogueHealth,
    DialogueStatistics,
)

logger = logging.getLogger(__name__)


class DialogueRuntime(IDialogueRuntime):
    """Thread-safe runtime manager for dialogue flow management."""

    def __init__(self, provider: Optional[IDialogueProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._initialized = False
        self._start_time: Optional[float] = None

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    def get_provider(self) -> Optional[IDialogueProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IDialogueProvider) -> None:
        """Register a dialogue provider instance thread-safely."""
        with self._lock:
            if not isinstance(provider, IDialogueProvider):
                raise TypeError("Provider must implement IDialogueProvider interface")
            self._provider = provider
            logger.debug("Registered dialogue provider: %s", provider)

    def initialize(self) -> None:
        """Initialize the Dialogue Runtime."""
        with self._lock:
            if self._initialized:
                return

            if self._provider is None:
                self._provider = DialogueProvider()

            if not self._provider.is_initialized:
                self._provider.initialize()

            self._initialized = True
            self._start_time = time.time()
            logger.info("DialogueRuntime initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down the Dialogue Runtime."""
        with self._lock:
            if not self._initialized:
                return

            if self._provider is not None and self._provider.is_initialized:
                self._provider.shutdown()

            self._initialized = False
            self._start_time = None
            logger.info("DialogueRuntime shutdown complete")

    def clear(self) -> None:
        """Reset dialogue runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._initialized = False
            self._start_time = None

    def get_health(self) -> DialogueHealth:
        """Return aggregated health status."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self._initialized
            return DialogueHealth(
                status="READY" if healthy else "UNINITIALIZED",
                healthy=healthy,
                subsystems={"provider": False},
                statistics={},
                detected_issues=[] if healthy else ["No provider registered"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> DialogueStatistics:
        """Return performance and usage statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return DialogueStatistics(
                total_sessions_created=0,
                active_sessions=0,
                total_turns_processed=0,
                clarifications_requested=0,
                confirmations_requested=0,
                average_turns_per_session=0.0,
                uptime_seconds=uptime,
                metadata={},
            )
