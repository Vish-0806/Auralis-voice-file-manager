"""Conversation Recovery & Persistence Manager for restoring sessions, contexts, and summaries.

This module provides thread-safe recovery tracking and state persistence management
without performing reasoning, calling LLMs, summarizing conversations, resolving references,
or executing commands.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional
import uuid

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.conversation.context_manager import ConversationContext, ConversationContextManager
from brain.conversation.conversation_session import ConversationSession, ConversationSessionManager
from brain.conversation.summarizer import ConversationSummarizer, ConversationSummary

logger = logging.getLogger(__name__)


class ConversationRecoveryStatus(str, Enum):
    """Enumeration representing recovery status states."""

    PENDING = "PENDING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    SKIPPED = "SKIPPED"


class ConversationRecoveryRecord(BaseModel):
    """Immutable model representing a recovery audit record for a session."""

    model_config = ConfigDict(frozen=True)

    recovery_id: str
    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recovered_at: Optional[datetime] = None
    status: ConversationRecoveryStatus = ConversationRecoveryStatus.PENDING
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationRecoveryConfig(BaseModel):
    """Configuration options for ConversationRecoveryManager limits and timeouts."""

    maximum_recovery_records: int = 1000
    recovery_timeout_seconds: int = 3600
    retention_limit: int = 5000
    automatic_cleanup: bool = True


class ConversationRecoveryManager:
    """Thread-safe manager for session, context, and summary recovery and audit tracking."""

    def __init__(self, config: Optional[ConversationRecoveryConfig] = None) -> None:
        """Initializes the recovery manager with optional configuration and thread lock."""
        self.config = config or ConversationRecoveryConfig()
        self._recovery_records: Dict[str, ConversationRecoveryRecord] = {}
        self._lock = threading.RLock()

    def create_recovery_record(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        recovery_id: Optional[str] = None,
    ) -> ConversationRecoveryRecord:
        """Creates and stores a new recovery tracking record."""
        with self._lock:
            if len(self._recovery_records) >= self.config.maximum_recovery_records:
                self._cleanup_locked()
                if len(self._recovery_records) >= self.config.maximum_recovery_records:
                    oldest_key = next(iter(self._recovery_records))
                    del self._recovery_records[oldest_key]

            rec_id = recovery_id or f"recovery_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)

            record = ConversationRecoveryRecord(
                recovery_id=rec_id,
                session_id=session_id,
                created_at=now,
                status=ConversationRecoveryStatus.PENDING,
                metadata=metadata or {},
            )
            self._recovery_records[rec_id] = record
            logger.info("Recovery Record Created: recovery_id=%s, session_id=%s", rec_id, session_id)
            return record

    def recover_session(
        self,
        session_id: str,
        session_manager: Optional[ConversationSessionManager] = None,
    ) -> Optional[ConversationSession]:
        """Validates eligibility and restores a conversation session from manager."""
        with self._lock:
            if session_manager is None:
                return None

            session = session_manager.get_session(session_id)
            if session is None:
                # Find pending record for session_id if any, and mark FAILED
                for rid, rec in list(self._recovery_records.items()):
                    if rec.session_id == session_id and rec.status == ConversationRecoveryStatus.PENDING:
                        self.mark_failed(rid, reason="Session not found in session manager")
                return None

            # Mark corresponding pending record as RECOVERED
            now = datetime.now(timezone.utc)
            for rid, rec in list(self._recovery_records.items()):
                if rec.session_id == session_id and rec.status == ConversationRecoveryStatus.PENDING:
                    self.mark_recovered(rid, reason="Session recovered successfully")

            logger.info("Conversation Recovered: session_id=%s", session_id)
            return session

    def recover_context(
        self,
        session_id: str,
        context_manager: Optional[ConversationContextManager] = None,
    ) -> Optional[ConversationContext]:
        """Restores associated conversation context from context manager."""
        with self._lock:
            if context_manager is None:
                return None
            return context_manager.get_context(session_id)

    def recover_summary(
        self,
        session_id: str,
        summarizer: Optional[ConversationSummarizer] = None,
    ) -> Optional[ConversationSummary]:
        """Restores associated summary from summarizer."""
        with self._lock:
            if summarizer is None:
                return None
            return summarizer.get_summary(session_id)

    def mark_recovered(self, recovery_id: str, reason: str = "") -> Optional[ConversationRecoveryRecord]:
        """Transitions a recovery record status to RECOVERED."""
        with self._lock:
            record = self._recovery_records.get(recovery_id)
            if record is None:
                return None

            now = datetime.now(timezone.utc)
            updated = ConversationRecoveryRecord(
                recovery_id=record.recovery_id,
                session_id=record.session_id,
                created_at=record.created_at,
                recovered_at=now,
                status=ConversationRecoveryStatus.RECOVERED,
                reason=reason or "Recovery completed",
                metadata=record.metadata,
            )
            self._recovery_records[recovery_id] = updated
            logger.info("Conversation Recovered: recovery_id=%s", recovery_id)
            return updated

    def mark_failed(self, recovery_id: str, reason: str = "") -> Optional[ConversationRecoveryRecord]:
        """Transitions a recovery record status to FAILED with reason."""
        with self._lock:
            record = self._recovery_records.get(recovery_id)
            if record is None:
                return None

            updated = ConversationRecoveryRecord(
                recovery_id=record.recovery_id,
                session_id=record.session_id,
                created_at=record.created_at,
                recovered_at=record.recovered_at,
                status=ConversationRecoveryStatus.FAILED,
                reason=reason or "Recovery failed",
                metadata=record.metadata,
            )
            self._recovery_records[recovery_id] = updated
            logger.info("Recovery Failed: recovery_id=%s, reason=%s", recovery_id, reason)
            return updated

    def mark_expired(self, recovery_id: str, reason: str = "") -> Optional[ConversationRecoveryRecord]:
        """Transitions a recovery record status to EXPIRED."""
        with self._lock:
            record = self._recovery_records.get(recovery_id)
            if record is None:
                return None

            updated = ConversationRecoveryRecord(
                recovery_id=record.recovery_id,
                session_id=record.session_id,
                created_at=record.created_at,
                recovered_at=record.recovered_at,
                status=ConversationRecoveryStatus.EXPIRED,
                reason=reason or "Recovery record expired",
                metadata=record.metadata,
            )
            self._recovery_records[recovery_id] = updated
            logger.info("Recovery Expired: recovery_id=%s", recovery_id)
            return updated

    def remove_record(self, recovery_id: str) -> bool:
        """Removes a recovery record by recovery_id."""
        with self._lock:
            if recovery_id in self._recovery_records:
                del self._recovery_records[recovery_id]
                logger.info("Recovery Record Removed: recovery_id=%s", recovery_id)
                return True
            return False

    def list_records(
        self,
        session_id: Optional[str] = None,
        status: Optional[ConversationRecoveryStatus] = None,
    ) -> List[ConversationRecoveryRecord]:
        """Lists recovery records, optionally filtered by session_id and/or status."""
        with self._lock:
            if self.config.automatic_cleanup:
                self._cleanup_locked()

            records = list(self._recovery_records.values())
            if session_id is not None:
                records = [r for r in records if r.session_id == session_id]
            if status is not None:
                records = [r for r in records if r.status == status]
            return records

    def cleanup(self, timeout_seconds: Optional[int] = None) -> int:
        """Removes expired records and enforces retention limits."""
        with self._lock:
            count = self._cleanup_locked(timeout_seconds)
            logger.info("Recovery Cleanup Completed: removed=%s", count)
            return count

    def clear(self) -> None:
        """Clears all recovery records."""
        with self._lock:
            self._recovery_records.clear()
            logger.info("Recovery Manager Cleared")

    def _cleanup_locked(self, timeout_seconds: Optional[int] = None) -> int:
        """Internal helper to clean up expired records and enforce retention limits under lock."""
        timeout = timeout_seconds if timeout_seconds is not None else self.config.recovery_timeout_seconds
        now = datetime.now(timezone.utc)
        removed_count = 0
        keys = list(self._recovery_records.keys())

        for rid in keys:
            rec = self._recovery_records[rid]
            if rec.status == ConversationRecoveryStatus.PENDING:
                elapsed = (now - rec.created_at).total_seconds()
                if elapsed > timeout:
                    del self._recovery_records[rid]
                    removed_count += 1

        while len(self._recovery_records) > self.config.retention_limit:
            oldest_key = next(iter(self._recovery_records))
            del self._recovery_records[oldest_key]
            removed_count += 1

        return removed_count
