"""Conversation Runtime Coordinator for integrating all Conversation Intelligence services.

This module provides thread-safe runtime lifecycle coordination, singleton service registration,
health monitoring, and runtime diagnostics without introducing new business logic, altering reasoning,
or calling LLMs.
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.conversation.context_manager import (
    ConversationContextConfig,
    ConversationContextManager,
)
from brain.conversation.conversation_session import (
    ConversationSessionConfig,
    ConversationSessionManager,
)
from brain.conversation.recovery import (
    ConversationRecoveryConfig,
    ConversationRecoveryManager,
    ConversationRecoveryStatus,
)
from brain.conversation.reference_resolver import (
    ConversationReferenceResolver,
    ReferenceResolverConfig,
)
from brain.conversation.summarizer import (
    ConversationSummarizer,
    ConversationSummaryConfig,
)

logger = logging.getLogger(__name__)


class ConversationRuntimeCoordinator:
    """Coordinator managing the lifecycle, registration, health, and diagnostics of conversation services."""

    def __init__(
        self,
        session_manager: Optional[ConversationSessionManager] = None,
        context_manager: Optional[ConversationContextManager] = None,
        reference_resolver: Optional[ConversationReferenceResolver] = None,
        summarizer: Optional[ConversationSummarizer] = None,
        recovery_manager: Optional[ConversationRecoveryManager] = None,
        session_config: Optional[ConversationSessionConfig] = None,
        context_config: Optional[ConversationContextConfig] = None,
        reference_config: Optional[ReferenceResolverConfig] = None,
        summary_config: Optional[ConversationSummaryConfig] = None,
        recovery_config: Optional[ConversationRecoveryConfig] = None,
    ) -> None:
        """Initializes the coordinator with custom or default manager instances."""
        self._lock = threading.RLock()
        self._initialized = False
        self._is_shutdown = False
        self._start_time: Optional[datetime] = None

        # Registered conversation managers (singletons)
        self._session_manager = session_manager or ConversationSessionManager(config=session_config)
        self._context_manager = context_manager or ConversationContextManager(config=context_config)
        self._reference_resolver = reference_resolver or ConversationReferenceResolver(config=reference_config)
        self._summarizer = summarizer or ConversationSummarizer(config=summary_config)
        self._recovery_manager = recovery_manager or ConversationRecoveryManager(config=recovery_config)

    @property
    def session_manager(self) -> ConversationSessionManager:
        return self._session_manager

    @property
    def context_manager(self) -> ConversationContextManager:
        return self._context_manager

    @property
    def reference_resolver(self) -> ConversationReferenceResolver:
        return self._reference_resolver

    @property
    def summarizer(self) -> ConversationSummarizer:
        return self._summarizer

    @property
    def recovery_manager(self) -> ConversationRecoveryManager:
        return self._recovery_manager

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    @property
    def is_shutdown(self) -> bool:
        with self._lock:
            return self._is_shutdown

    def initialize(self) -> bool:
        """Initializes the conversation runtime idempotently."""
        with self._lock:
            if self._initialized:
                logger.info("Conversation Runtime already initialized")
                return True

            self._initialized = True
            self._is_shutdown = False
            self._start_time = datetime.now(timezone.utc)
            logger.info("Conversation Runtime Initialized")
            return True

    def shutdown(self) -> bool:
        """Shuts down the conversation runtime safely."""
        with self._lock:
            if self._is_shutdown:
                logger.info("Conversation Runtime already shutdown")
                return True

            self._is_shutdown = True
            self._initialized = False
            logger.info("Conversation Runtime Shutdown")
            return True

    def health_check(self) -> Dict[str, Any]:
        """Validates runtime health status and service counts."""
        with self._lock:
            is_healthy = self._initialized and not self._is_shutdown
            status = "HEALTHY" if is_healthy else ("SHUTDOWN" if self._is_shutdown else "NOT_INITIALIZED")

            active_sessions = len(self._session_manager.list_active_sessions())
            active_contexts = len(self._context_manager.list_contexts())
            active_summaries = len(self._summarizer.list_summaries())
            pending_recoveries = len(
                self._recovery_manager.list_records(status=ConversationRecoveryStatus.PENDING)
            )

            result = {
                "overall_status": status,
                "registered_services": [
                    "ConversationSessionManager",
                    "ConversationContextManager",
                    "ConversationReferenceResolver",
                    "ConversationSummarizer",
                    "ConversationRecoveryManager",
                ],
                "active_sessions": active_sessions,
                "active_contexts": active_contexts,
                "active_summaries": active_summaries,
                "pending_recoveries": pending_recoveries,
                "thread_safety_status": "PROTECTED",
            }
            logger.info("Conversation Runtime Health Check")
            return result

    def runtime_statistics(self) -> Dict[str, Any]:
        """Generates runtime diagnostic statistics."""
        with self._lock:
            now = datetime.now(timezone.utc)
            uptime = (now - self._start_time).total_seconds() if (self._start_time and self._initialized) else 0.0

            active_sessions_list = self._session_manager.list_active_sessions()
            all_sessions_list = self._session_manager.list_sessions()
            contexts_list = self._context_manager.list_contexts()
            summaries_list = self._summarizer.list_summaries()
            recovery_records = self._recovery_manager.list_records()

            result = {
                "service_count": 5,
                "registered_components": [
                    "ConversationSessionManager",
                    "ConversationContextManager",
                    "ConversationReferenceResolver",
                    "ConversationSummarizer",
                    "ConversationRecoveryManager",
                ],
                "session_statistics": {
                    "total_sessions": len(all_sessions_list),
                    "active_sessions": len(active_sessions_list),
                    "completed_sessions": len(all_sessions_list) - len(active_sessions_list),
                },
                "context_statistics": {
                    "total_contexts": len(contexts_list),
                },
                "summary_statistics": {
                    "total_summaries": len(summaries_list),
                },
                "recovery_statistics": {
                    "total_records": len(recovery_records),
                    "pending_records": len([r for r in recovery_records if r.status == ConversationRecoveryStatus.PENDING]),
                    "recovered_records": len([r for r in recovery_records if r.status == ConversationRecoveryStatus.RECOVERED]),
                    "failed_records": len([r for r in recovery_records if r.status == ConversationRecoveryStatus.FAILED]),
                    "expired_records": len([r for r in recovery_records if r.status == ConversationRecoveryStatus.EXPIRED]),
                },
                "uptime": uptime,
            }
            logger.info("Conversation Runtime Statistics Generated")
            return result

    def clear(self) -> None:
        """Clears all conversation service states."""
        with self._lock:
            self._session_manager.clear()
            self._context_manager.clear()
            self._reference_resolver.clear()
            self._summarizer.clear()
            self._recovery_manager.clear()
            self._start_time = datetime.now(timezone.utc) if self._initialized else None


_global_lock = threading.RLock()
_global_runtime_instance: Optional[ConversationRuntimeCoordinator] = None


def get_conversation_runtime(
    session_config: Optional[ConversationSessionConfig] = None,
    context_config: Optional[ConversationContextConfig] = None,
    reference_config: Optional[ReferenceResolverConfig] = None,
    summary_config: Optional[ConversationSummaryConfig] = None,
    recovery_config: Optional[ConversationRecoveryConfig] = None,
    reset: bool = False,
) -> ConversationRuntimeCoordinator:
    """Singleton accessor for the ConversationRuntimeCoordinator instance."""
    global _global_runtime_instance
    with _global_lock:
        if reset or _global_runtime_instance is None:
            _global_runtime_instance = ConversationRuntimeCoordinator(
                session_config=session_config,
                context_config=context_config,
                reference_config=reference_config,
                summary_config=summary_config,
                recovery_config=recovery_config,
            )
            _global_runtime_instance.initialize()
        return _global_runtime_instance


def reset_conversation_runtime() -> None:
    """Resets the global ConversationRuntimeCoordinator instance."""
    global _global_runtime_instance
    with _global_lock:
        if _global_runtime_instance is not None:
            _global_runtime_instance.shutdown()
            _global_runtime_instance.clear()
            _global_runtime_instance = None
