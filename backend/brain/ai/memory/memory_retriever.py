"""DefaultMemoryRetriever for scope-aware AI memory retrieval (Phase 10.5).

Extracts and normalizes session, recent, long-term, and pinned memories from AIContext.
"""

import uuid
import logging
from typing import Any, List, Optional

from brain.ai.ai_models import AIContext
from brain.ai.memory.exceptions import MemoryRetrievalError
from brain.ai.memory.interfaces import MemoryRetrieverInterface
from brain.ai.memory.memory_models import AIMemoryItem, MemoryScope

logger = logging.getLogger(__name__)


class DefaultMemoryRetriever(MemoryRetrieverInterface):
    """Concrete implementation of MemoryRetrieverInterface."""

    def retrieve(
        self,
        context: AIContext,
        scopes: Optional[List[MemoryScope]] = None,
    ) -> List[AIMemoryItem]:
        """Retrieve memory items across requested memory scopes.

        Args:
            context: Incoming AIContext snapshot.
            scopes: Optional list of MemoryScope filters. Defaults to all scopes.

        Returns:
            List of normalized AIMemoryItem objects.

        Raises:
            MemoryRetrievalError: If retrieval processing encounters invalid structures.
        """
        try:
            target_scopes = set(scopes) if scopes else set(MemoryScope)
            items: List[AIMemoryItem] = []

            mem_dict = context.memory_context if context.memory_context else {}
            exec_dict = context.execution_context if context.execution_context else {}

            # 1. Pinned Memories (Highest Importance)
            if MemoryScope.PINNED in target_scopes and "pinned" in mem_dict:
                items.extend(self._extract_items(mem_dict["pinned"], MemoryScope.PINNED, importance=1.0, facet="pinned"))

            # 2. Session Memories
            if MemoryScope.SESSION in target_scopes:
                session_val = mem_dict.get("session", exec_dict.get("session_memory"))
                if session_val:
                    items.extend(self._extract_items(session_val, MemoryScope.SESSION, importance=0.85, facet="session"))

            # 3. Execution Context State
            if exec_dict:
                items.extend(self._extract_items(exec_dict, MemoryScope.SESSION, key_prefix="execution", importance=0.8, facet="execution"))

            # 4. User Preferences
            pref_val = mem_dict.get("user_preferences", mem_dict.get("preferences"))
            if pref_val:
                items.extend(self._extract_items(pref_val, MemoryScope.LONG_TERM, key_prefix="preferences", importance=0.7, facet="preferences"))

            # 5. Recent Memories
            if MemoryScope.RECENT in target_scopes and "recent" in mem_dict:
                items.extend(self._extract_items(mem_dict["recent"], MemoryScope.RECENT, importance=0.6, facet="recent"))

            # 6. Long-Term Memories
            if MemoryScope.LONG_TERM in target_scopes and "long_term" in mem_dict:
                items.extend(self._extract_items(mem_dict["long_term"], MemoryScope.LONG_TERM, importance=0.5, facet="long_term"))

            # 7. Generic Fallback for custom keys
            for key, val in mem_dict.items():
                if key not in ("pinned", "session", "recent", "long_term", "preferences", "user_preferences"):
                    if MemoryScope.LONG_TERM in target_scopes or MemoryScope.RECENT in target_scopes:
                        items.extend(self._extract_items(val, MemoryScope.LONG_TERM, key_prefix=key, importance=0.4, facet="long_term"))

            return items
        except Exception as exc:
            raise MemoryRetrievalError(f"Failed to retrieve memory items: {exc}") from exc

    def _extract_items(
        self,
        raw_val: Any,
        scope: MemoryScope,
        key_prefix: str = "",
        importance: float = 0.5,
        facet: str = "long_term",
    ) -> List[AIMemoryItem]:
        """Normalize various raw Python structures into AIMemoryItem models."""
        items: List[AIMemoryItem] = []
        prefix = key_prefix or scope.value

        if isinstance(raw_val, str):
            if raw_val.strip() and raw_val.strip() != "None":
                content_str = f"{key_prefix}: {raw_val.strip()}" if key_prefix else raw_val.strip()
                items.append(
                    AIMemoryItem(
                        memory_id=f"mem-{uuid.uuid4().hex[:8]}",
                        key=prefix,
                        content=content_str,
                        scope=scope,
                        importance_score=importance,
                        metadata={"facet": facet},
                    )
                )
        elif isinstance(raw_val, list):
            for idx, entry in enumerate(raw_val):
                if isinstance(entry, str):
                    if entry.strip() and entry.strip() != "None":
                        items.append(
                            AIMemoryItem(
                                memory_id=f"mem-{uuid.uuid4().hex[:8]}",
                                key=f"{prefix}_{idx}",
                                content=entry.strip(),
                                scope=scope,
                                importance_score=importance,
                                metadata={"facet": facet},
                            )
                        )
                elif isinstance(entry, dict):
                    k = entry.get("key", f"{prefix}_{idx}")
                    c = entry.get("content") or entry.get("value") or str(entry)
                    imp = float(entry.get("importance", importance))
                    items.append(
                        AIMemoryItem(
                            memory_id=str(entry.get("id", f"mem-{uuid.uuid4().hex[:8]}")),
                            key=str(k),
                            content=str(c),
                            scope=scope,
                            importance_score=imp,
                            metadata={"facet": facet, **entry.get("metadata", {})},
                        )
                    )
        elif isinstance(raw_val, dict):
            for k, v in raw_val.items():
                content_str = str(v)
                if content_str.strip() and content_str.strip() != "None":
                    items.append(
                        AIMemoryItem(
                            memory_id=f"mem-{uuid.uuid4().hex[:8]}",
                            key=f"{prefix}_{k}",
                            content=f"{k}: {content_str}",
                            scope=scope,
                            importance_score=importance,
                            metadata={"facet": facet},
                        )
                    )

        return items
