"""Conversation Runtime Coordinator for Auralis (Phase 13.2).

Manages runtime lifecycle, provider registration, health monitoring, statistics,
and thread safety using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Optional

from brain.assistant.conversation.conversation_provider import ConversationProvider
from brain.assistant.conversation.interfaces import (
    IConversationProvider,
    IConversationRuntime,
)
from brain.assistant.conversation.models import (
    ConversationHealth,
    ConversationStatistics,
)

logger = logging.getLogger(__name__)


class ConversationRuntime(IConversationRuntime):
    """Thread-safe runtime coordinator for conversation management."""

    def __init__(self, provider: Optional[IConversationProvider] = None) -> None:
        self._lock = threading.RLock()
        self._provider = provider
        self._initialized = False
        self._start_time: Optional[float] = None

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    def get_provider(self) -> Optional[IConversationProvider]:
        with self._lock:
            return self._provider

    def register_provider(self, provider: IConversationProvider) -> None:
        """Register a conversation provider instance thread-safely."""
        with self._lock:
            if not isinstance(provider, IConversationProvider):
                raise TypeError("Provider must implement IConversationProvider interface")
            self._provider = provider
            logger.debug("Registered conversation provider: %s", provider)

    def initialize(self) -> None:
        """Initialize the Conversation Runtime."""
        with self._lock:
            if self._initialized:
                return

            if self._provider is None:
                self._provider = ConversationProvider()

            if not self._provider.is_initialized:
                self._provider.initialize()

            self._initialized = True
            self._start_time = time.time()
            logger.info("ConversationRuntime initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down the Conversation Runtime."""
        with self._lock:
            if not self._initialized:
                return

            if self._provider is not None and self._provider.is_initialized:
                self._provider.shutdown()

            self._initialized = False
            self._start_time = None
            logger.info("ConversationRuntime shutdown complete")

    def clear(self) -> None:
        """Reset conversation runtime state and statistics."""
        with self._lock:
            if self._provider is not None and hasattr(self._provider, "clear"):
                self._provider.clear()  # type: ignore[attr-defined]
            self._initialized = False
            self._start_time = None

    def get_health(self) -> ConversationHealth:
        """Return aggregated health status."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_health()

            healthy = self._initialized
            return ConversationHealth(
                status="READY" if healthy else "UNINITIALIZED",
                healthy=healthy,
                subsystems={"provider": False},
                statistics={},
                detected_issues=[] if healthy else ["No provider registered"],
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> ConversationStatistics:
        """Return performance and usage statistics."""
        with self._lock:
            if self._provider is not None:
                return self._provider.get_statistics()

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return ConversationStatistics(
                total_conversations_created=0,
                active_conversations=0,
                closed_conversations=0,
                archived_conversations=0,
                total_messages_processed=0,
                average_messages_per_conversation=0.0,
                uptime_seconds=uptime,
                metadata={},
            )
