"""Conversation Context Manager for maintaining active conversational context per session.

This module provides thread-safe context window management without performing reasoning,
LLM calls, conversation summarization, or reference resolution.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.conversation.conversation_session import ConversationTurn

logger = logging.getLogger(__name__)


class ConversationContext(BaseModel):
    """Immutable snapshot model representing the active conversational context window."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    context_window: List[ConversationTurn] = Field(default_factory=list)
    max_context_turns: int = 20
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationContextConfig(BaseModel):
    """Configuration options for ConversationContextManager limits and timeouts."""

    default_context_window: int = 20
    maximum_context_window: int = 100
    maximum_contexts: int = 500
    context_timeout_seconds: int = 3600


class ConversationContextManager:
    """Thread-safe manager responsible for maintaining active conversation contexts.

    Internal storage uses RLock protection for all creation, update, insertion,
    resizing, cleanup, expiration, and listing operations.
    """

    def __init__(self, config: Optional[ConversationContextConfig] = None) -> None:
        """Initializes the context manager with optional configuration and thread lock."""
        self.config = config or ConversationContextConfig()
        self._contexts: Dict[str, ConversationContext] = {}
        self._lock = threading.RLock()

    def create_context(
        self,
        session_id: str,
        max_context_turns: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationContext:
        """Creates and associates an empty context window for a session."""
        with self._lock:
            # Enforce capacity limit
            if len(self._contexts) >= self.config.maximum_contexts:
                self._expire_contexts_locked()
                if len(self._contexts) >= self.config.maximum_contexts:
                    oldest_key = next(iter(self._contexts))
                    del self._contexts[oldest_key]

            raw_window = max_context_turns if max_context_turns is not None else self.config.default_context_window
            effective_max = max(1, min(raw_window, self.config.maximum_context_window))
            now = datetime.now(timezone.utc)

            context = ConversationContext(
                session_id=session_id,
                context_window=[],
                max_context_turns=effective_max,
                last_updated=now,
                metadata=metadata or {},
            )
            self._contexts[session_id] = context
            logger.info("Conversation Context Created: session_id=%s", session_id)
            return context

    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Retrieves an immutable snapshot of context for session_id, checking expiration."""
        with self._lock:
            ctx = self._contexts.get(session_id)
            if ctx is None:
                return None

            elapsed = (datetime.now(timezone.utc) - ctx.last_updated).total_seconds()
            if elapsed > self.config.context_timeout_seconds:
                del self._contexts[session_id]
                logger.info("Conversation Context Expired: session_id=%s", session_id)
                return None

            return ctx

    def update_context(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ConversationContext]:
        """Refreshes context timestamp and merges metadata into existing context."""
        with self._lock:
            ctx = self.get_context(session_id)
            if ctx is None:
                return None

            now = datetime.now(timezone.utc)
            merged_meta = {**ctx.metadata, **(metadata or {})}
            updated = ConversationContext(
                session_id=ctx.session_id,
                context_window=ctx.context_window,
                max_context_turns=ctx.max_context_turns,
                last_updated=now,
                metadata=merged_meta,
            )
            self._contexts[session_id] = updated
            logger.info("Conversation Context Updated: session_id=%s", session_id)
            return updated

    def append_turn(
        self,
        session_id: str,
        turn: ConversationTurn,
    ) -> Optional[ConversationContext]:
        """Appends a turn to context window, maintaining chronological order and sliding window limit."""
        with self._lock:
            ctx = self.get_context(session_id)
            if ctx is None:
                return None

            new_window = list(ctx.context_window) + [turn]
            if len(new_window) > ctx.max_context_turns:
                new_window = new_window[-ctx.max_context_turns:]

            now = datetime.now(timezone.utc)
            updated = ConversationContext(
                session_id=ctx.session_id,
                context_window=new_window,
                max_context_turns=ctx.max_context_turns,
                last_updated=now,
                metadata=ctx.metadata,
            )
            self._contexts[session_id] = updated
            logger.info("Conversation Turn Added To Context: session_id=%s, turn_id=%s", session_id, turn.turn_id)
            return updated

    def get_recent_turns(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[ConversationTurn]:
        """Returns recent turns for session_id in chronological order, optionally capped by limit."""
        with self._lock:
            ctx = self.get_context(session_id)
            if ctx is None:
                return []

            turns = ctx.context_window
            if limit is not None and limit > 0:
                return list(turns[-limit:])
            return list(turns)

    def resize_context_window(
        self,
        session_id: str,
        new_max_turns: int,
    ) -> Optional[ConversationContext]:
        """Resizes max context window cap, discarding oldest turns if current window exceeds cap."""
        with self._lock:
            ctx = self.get_context(session_id)
            if ctx is None:
                return None

            new_cap = max(1, min(new_max_turns, self.config.maximum_context_window))
            new_window = list(ctx.context_window)
            if len(new_window) > new_cap:
                new_window = new_window[-new_cap:]

            now = datetime.now(timezone.utc)
            updated = ConversationContext(
                session_id=ctx.session_id,
                context_window=new_window,
                max_context_turns=new_cap,
                last_updated=now,
                metadata=ctx.metadata,
            )
            self._contexts[session_id] = updated
            logger.info("Conversation Context Resized: session_id=%s, new_max_turns=%s", session_id, new_cap)
            return updated

    def clear_context(self, session_id: str) -> bool:
        """Clears all turns from the context window for session_id."""
        with self._lock:
            ctx = self._contexts.get(session_id)
            if ctx is None:
                return False

            now = datetime.now(timezone.utc)
            updated = ConversationContext(
                session_id=ctx.session_id,
                context_window=[],
                max_context_turns=ctx.max_context_turns,
                last_updated=now,
                metadata=ctx.metadata,
            )
            self._contexts[session_id] = updated
            logger.info("Conversation Context Cleared: session_id=%s", session_id)
            return True

    def remove_context(self, session_id: str) -> bool:
        """Removes context entry for session_id completely."""
        with self._lock:
            if session_id in self._contexts:
                del self._contexts[session_id]
                logger.info("Conversation Context Removed: session_id=%s", session_id)
                return True
            return False

    def expire_contexts(self, timeout_seconds: Optional[int] = None) -> List[str]:
        """Scans contexts and removes inactive ones past the timeout threshold."""
        with self._lock:
            return self._expire_contexts_locked(timeout_seconds)

    def list_contexts(self) -> List[ConversationContext]:
        """Returns list of active non-expired context snapshots."""
        with self._lock:
            self._expire_contexts_locked()
            return list(self._contexts.values())

    def clear(self) -> None:
        """Clears all managed context entries."""
        with self._lock:
            self._contexts.clear()
            logger.info("Conversation Context Manager Cleared")

    def _expire_contexts_locked(self, timeout_seconds: Optional[int] = None) -> List[str]:
        """Internal helper to remove expired contexts under lock."""
        timeout = timeout_seconds if timeout_seconds is not None else self.config.context_timeout_seconds
        now = datetime.now(timezone.utc)
        expired_ids: List[str] = []
        keys = list(self._contexts.keys())

        for sid in keys:
            ctx = self._contexts[sid]
            elapsed = (now - ctx.last_updated).total_seconds()
            if elapsed > timeout:
                del self._contexts[sid]
                logger.info("Conversation Context Expired: session_id=%s", sid)
                expired_ids.append(sid)

        return expired_ids
