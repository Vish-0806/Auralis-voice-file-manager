"""Conversation Provider for Auralis (Phase 13.2).

Aggregates ConversationManager, HistoryManager, and ContextManager into a unified gateway.
Exposes health reports, metrics statistics, and capabilities using constructor dependency injection only.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.assistant.conversation.context_manager import ContextManager
from brain.assistant.conversation.conversation_manager import ConversationManager
from brain.assistant.conversation.history_manager import HistoryManager
from brain.assistant.conversation.interfaces import (
    IConversationContextManager,
    IConversationHistoryManager,
    IConversationManager,
    IConversationProvider,
)
from brain.assistant.conversation.models import (
    ConversationHealth,
    ConversationState,
    ConversationStatistics,
)

logger = logging.getLogger(__name__)


class ConversationProvider(IConversationProvider):
    """Aggregating provider for conversation lifecycle, history, and context subsystems."""

    def __init__(
        self,
        manager: Optional[IConversationManager] = None,
        history_manager: Optional[IConversationHistoryManager] = None,
        context_manager: Optional[IConversationContextManager] = None,
    ) -> None:
        """Initializes ConversationProvider with constructor dependency injection only."""
        self._lock = threading.RLock()
        self._manager = manager or ConversationManager(lock=self._lock)
        self._history_manager = history_manager or HistoryManager(lock=self._lock)
        self._context_manager = context_manager or ContextManager(lock=self._lock)

        self._initialized = False
        self._start_time: Optional[float] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def manager(self) -> IConversationManager:
        with self._lock:
            return self._manager

    @property
    def history_manager(self) -> IConversationHistoryManager:
        with self._lock:
            return self._history_manager

    @property
    def context_manager(self) -> IConversationContextManager:
        with self._lock:
            return self._context_manager

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize provider resources."""
        with self._lock:
            if self._initialized:
                return

            self._initialized = True
            self._start_time = time.time()
            logger.info("ConversationProvider initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shutdown provider resources."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False
            self._start_time = None
            logger.info("ConversationProvider shutdown complete")

    def clear(self) -> None:
        """Reset conversation managers, history, and statistics."""
        with self._lock:
            if hasattr(self._manager, "clear"):
                self._manager.clear()  # type: ignore[union-attr]
            if hasattr(self._history_manager, "clear"):
                self._history_manager.clear()  # type: ignore[union-attr]
            if hasattr(self._context_manager, "clear"):
                self._context_manager.clear()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def get_health(self) -> ConversationHealth:
        """Expose real-time diagnostic health status."""
        with self._lock:
            subsystems = {
                "manager": self._manager is not None,
                "history_manager": self._history_manager is not None,
                "context_manager": self._context_manager is not None,
            }
            issues: List[str] = []
            if not self._initialized:
                issues.append("ConversationProvider is not initialized")

            healthy = self._initialized and len(issues) == 0

            return ConversationHealth(
                status="READY" if healthy else ("UNINITIALIZED" if not self._initialized else "DEGRADED"),
                healthy=healthy,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> ConversationStatistics:
        """Expose aggregated statistics across all conversations and histories."""
        with self._lock:
            all_convs = self._manager.list_conversations() if self._manager else []
            total_created = len(all_convs)
            active_count = len([c for c in all_convs if c.state == ConversationState.ACTIVE])
            closed_count = len([c for c in all_convs if c.state == ConversationState.CLOSED])
            archived_count = len([c for c in all_convs if c.state == ConversationState.ARCHIVED])

            total_messages = 0
            if self._history_manager:
                for c in all_convs:
                    hist = self._history_manager.get_history(c.conversation_id)
                    total_messages += hist.total_messages

            avg_messages = (total_messages / total_created) if total_created > 0 else 0.0

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return ConversationStatistics(
                total_conversations_created=total_created,
                active_conversations=active_count,
                closed_conversations=closed_count,
                archived_conversations=archived_count,
                total_messages_processed=total_messages,
                average_messages_per_conversation=avg_messages,
                uptime_seconds=uptime,
                metadata={},
            )
