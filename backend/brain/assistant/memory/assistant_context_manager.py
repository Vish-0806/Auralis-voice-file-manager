"""Assistant Context Manager implementation for Auralis (Phase 13.5).

Retrieves, merges, prioritizes, deduplicates, and token-budgets context units from multiple subsystems.
Does NOT call AI or perform vector search. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional, Set

from brain.assistant.memory.exceptions import AssistantContextMergeError, AssistantMemoryValidationError
from brain.assistant.memory.interfaces import IAssistantContextManager
from brain.assistant.memory.models import (
    AssistantContextPriority,
    AssistantMemoryContext,
    AssistantWorkingContext,
)

logger = logging.getLogger(__name__)

_PRIORITY_RANK = {
    AssistantContextPriority.MANDATORY: 5,
    AssistantContextPriority.CRITICAL: 4,
    AssistantContextPriority.HIGH: 3,
    AssistantContextPriority.MEDIUM: 2,
    AssistantContextPriority.LOW: 1,
}


class AssistantContextManager(IAssistantContextManager):
    """Thread-safe context manager for prioritizing, deduplicating, and merging subsystem contexts."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._duplicates_removed = 0
        self._trims_count = 0

    @property
    def duplicates_removed_count(self) -> int:
        with self._lock:
            return self._duplicates_removed

    @property
    def trims_count(self) -> int:
        with self._lock:
            return self._trims_count

    def merge_contexts(
        self,
        contexts: List[AssistantMemoryContext],
        session_id: Optional[str] = None,
        token_budget: int = 4096,
    ) -> AssistantWorkingContext:
        """Merge, prioritize, deduplicate, and token-budget context units into an AssistantWorkingContext."""
        if not isinstance(contexts, list):
            raise AssistantMemoryValidationError("contexts must be a list of AssistantMemoryContext objects")

        with self._lock:
            # 1. Priority Sorting (Higher priority rank first)
            sorted_contexts = sorted(
                contexts,
                key=lambda c: _PRIORITY_RANK.get(c.priority, 2),
                reverse=True,
            )

            merged_vars: Dict[str, Any] = {}
            seen_keys: Set[str] = set()
            included_contexts: List[AssistantMemoryContext] = []
            accumulated_tokens = 0
            trimmed = False

            # 2. Deduplication and Token Budgeting
            for ctx in sorted_contexts:
                # Calculate tokens estimate for context payload
                ctx_tokens = ctx.tokens_estimate or max(1, len(str(ctx.payload)) // 4)

                if accumulated_tokens + ctx_tokens > token_budget:
                    trimmed = True
                    self._trims_count += 1
                    logger.debug("Token budget %d exceeded; trimming lower priority context %s", token_budget, ctx.context_id)
                    continue

                # Deduplicate payload variables (higher priority wins)
                for k, v in ctx.payload.items():
                    if k in seen_keys:
                        self._duplicates_removed += 1
                    else:
                        seen_keys.add(k)
                        merged_vars[k] = v

                accumulated_tokens += ctx_tokens
                included_contexts.append(ctx)

            working_ctx = AssistantWorkingContext(
                session_id=session_id,
                merged_variables=merged_vars,
                prioritized_contexts=included_contexts,
                total_tokens_estimate=accumulated_tokens,
                token_budget=token_budget,
                trimmed=trimmed,
                merged_at=datetime.now(timezone.utc),
            )

            logger.debug("Merged %d contexts into working_ctx_id=%s (tokens=%d, trimmed=%s)", len(included_contexts), working_ctx.working_context_id, accumulated_tokens, trimmed)
            return working_ctx
