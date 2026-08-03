"""Memory Coordinator implementation for Auralis (Phase 13.5).

Coordinates context retrieval across Conversation, Dialogue, Decision, Execution, and AI Memory runtimes.
Produces unified AssistantMemorySnapshot with priority ordering without AI calls. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.assistant.memory.assistant_context_manager import AssistantContextManager
from brain.assistant.memory.interfaces import IAssistantMemoryCoordinator
from brain.assistant.memory.models import (
    AssistantContextPriority,
    AssistantConversationSummary,
    AssistantMemoryContext,
    AssistantMemoryReference,
    AssistantMemoryScope,
    AssistantMemorySnapshot,
    AssistantMemorySource,
    AssistantWorkingContext,
)

logger = logging.getLogger(__name__)


class MemoryCoordinator(IAssistantMemoryCoordinator):
    """Thread-safe coordinator producing unified AssistantMemorySnapshot views across subsystem runtimes."""

    def __init__(
        self,
        context_manager: Optional[AssistantContextManager] = None,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self._lock = lock or threading.RLock()
        self._context_manager = context_manager or AssistantContextManager(lock=self._lock)

    def create_snapshot(
        self,
        session_id: Optional[str] = None,
        conversation_runtime: Optional[Any] = None,
        dialogue_runtime: Optional[Any] = None,
        decision_runtime: Optional[Any] = None,
        execution_runtime: Optional[Any] = None,
        ai_memory_runtime: Optional[Any] = None,
        token_budget: int = 4096,
    ) -> AssistantMemorySnapshot:
        """Collect context from registered runtimes and synthesize a unified AssistantMemorySnapshot."""
        with self._lock:
            collected_contexts: List[AssistantMemoryContext] = []
            references: List[AssistantMemoryReference] = []

            conv_summary: Optional[AssistantConversationSummary] = None
            dial_status_str: Optional[str] = None
            last_action_str: Optional[str] = None

            # 1. Inspect Conversation Runtime
            if conversation_runtime is not None:
                try:
                    stats = conversation_runtime.get_statistics()
                    collected_contexts.append(
                        AssistantMemoryContext(
                            source=AssistantMemorySource.CONVERSATION_RUNTIME,
                            scope=AssistantMemoryScope.CONVERSATION,
                            priority=AssistantContextPriority.HIGH,
                            payload={"active_conversations": stats.active_conversations},
                            tokens_estimate=20,
                        )
                    )
                    references.append(
                        AssistantMemoryReference(
                            source=AssistantMemorySource.CONVERSATION_RUNTIME,
                            source_key="active_conversations",
                            priority=AssistantContextPriority.HIGH,
                            tokens_estimate=20,
                        )
                    )
                    conv_summary = AssistantConversationSummary(
                        title="Integrated Session",
                        message_count=stats.total_messages_processed,
                        last_activity=datetime.now(timezone.utc),
                    )
                except Exception as exc:
                    logger.debug("Failed to inspect conversation_runtime: %s", exc)

            # 2. Inspect Dialogue Runtime
            if dialogue_runtime is not None:
                try:
                    health = dialogue_runtime.get_health()
                    dial_status_str = health.status
                    collected_contexts.append(
                        AssistantMemoryContext(
                            source=AssistantMemorySource.DIALOGUE_RUNTIME,
                            scope=AssistantMemoryScope.SESSION,
                            priority=AssistantContextPriority.CRITICAL,
                            payload={"dialogue_status": dial_status_str},
                            tokens_estimate=15,
                        )
                    )
                    references.append(
                        AssistantMemoryReference(
                            source=AssistantMemorySource.DIALOGUE_RUNTIME,
                            source_key="dialogue_status",
                            priority=AssistantContextPriority.CRITICAL,
                            tokens_estimate=15,
                        )
                    )
                except Exception as exc:
                    logger.debug("Failed to inspect dialogue_runtime: %s", exc)

            # 3. Inspect Decision Runtime
            if decision_runtime is not None:
                try:
                    stats = decision_runtime.get_statistics()
                    collected_contexts.append(
                        AssistantMemoryContext(
                            source=AssistantMemorySource.DECISION_RUNTIME,
                            scope=AssistantMemoryScope.SESSION,
                            priority=AssistantContextPriority.MANDATORY,
                            payload={"total_decisions_evaluated": stats.total_requests_evaluated},
                            tokens_estimate=15,
                        )
                    )
                    last_action_str = "EVALUATED"
                except Exception as exc:
                    logger.debug("Failed to inspect decision_runtime: %s", exc)

            # 4. Inspect Execution Runtime
            if execution_runtime is not None:
                try:
                    stats = execution_runtime.get_statistics()
                    collected_contexts.append(
                        AssistantMemoryContext(
                            source=AssistantMemorySource.EXECUTION_RUNTIME,
                            scope=AssistantMemoryScope.SESSION,
                            priority=AssistantContextPriority.HIGH,
                            payload={"active_execution_sessions": getattr(stats, "active_sessions", 0)},
                            tokens_estimate=15,
                        )
                    )
                except Exception as exc:
                    logger.debug("Failed to inspect execution_runtime: %s", exc)

            # 5. Inspect AI Memory Runtime
            if ai_memory_runtime is not None:
                try:
                    collected_contexts.append(
                        AssistantMemoryContext(
                            source=AssistantMemorySource.AI_MEMORY_RUNTIME,
                            scope=AssistantMemoryScope.USER,
                            priority=AssistantContextPriority.MEDIUM,
                            payload={"ai_memory_attached": True},
                            tokens_estimate=10,
                        )
                    )
                except Exception as exc:
                    logger.debug("Failed to inspect ai_memory_runtime: %s", exc)

            # Synthesize working context via ContextManager
            working_ctx = self._context_manager.merge_contexts(
                collected_contexts,
                session_id=session_id,
                token_budget=token_budget,
            )

            snapshot = AssistantMemorySnapshot(
                session_id=session_id,
                conversation_summary=conv_summary,
                dialogue_status=dial_status_str,
                last_decision_action=last_action_str,
                working_context=working_ctx,
                references=references,
                created_at=datetime.now(timezone.utc),
                metadata={"subsystems_inspected": len(collected_contexts)},
            )

            logger.info("Generated AssistantMemorySnapshot id=%s for session_id=%s", snapshot.snapshot_id, session_id)
            return snapshot
