"""AIMemoryProvider implementation connecting backend memory subsystem to AI runtime (Phase 10.5).

Abstracts memory retrieval, ranking, and filtering into a unified pipeline.
Implements AIMemoryProviderInterface and MemoryProviderInterface for MemoryInjector integration.
"""

import logging
from typing import Any, Dict, List, Optional

from brain.ai.ai_models import AIContext
from brain.ai.memory.interfaces import (
    AIMemoryProviderInterface,
    MemoryFilterInterface,
    MemoryRankerInterface,
    MemoryRetrieverInterface,
)
from brain.ai.memory.memory_filter import DefaultMemoryFilter
from brain.ai.memory.memory_models import AIMemoryItem, MemoryQueryResult, MemoryScope
from brain.ai.memory.memory_ranker import DefaultMemoryRanker
from brain.ai.memory.memory_retriever import DefaultMemoryRetriever
from brain.ai.memory_injector import MemoryProviderInterface

logger = logging.getLogger(__name__)


class AIMemoryProvider(AIMemoryProviderInterface, MemoryProviderInterface):
    """Unified memory provider wrapping retrieval, ranking, and filtering pipeline."""

    def __init__(
        self,
        retriever: Optional[MemoryRetrieverInterface] = None,
        ranker: Optional[MemoryRankerInterface] = None,
        filter_engine: Optional[MemoryFilterInterface] = None,
    ) -> None:
        self.retriever = retriever or DefaultMemoryRetriever()
        self.ranker = ranker or DefaultMemoryRanker()
        self.filter_engine = filter_engine or DefaultMemoryFilter()

    def fetch_memories(
        self,
        context: AIContext,
        scopes: Optional[List[MemoryScope]] = None,
    ) -> List[AIMemoryItem]:
        """Fetch raw AIMemoryItem objects across scopes."""
        return self.retriever.retrieve(context, scopes=scopes)

    def query_memories(
        self,
        context: AIContext,
        query: str = "",
        max_results: int = 10,
        max_tokens: Optional[int] = None,
        scopes: Optional[List[MemoryScope]] = None,
    ) -> MemoryQueryResult:
        """Query, rank, filter, and package memory items into a MemoryQueryResult model.

        Args:
            context: Incoming AIContext snapshot.
            query: Query text string.
            max_results: Maximum items limit.
            max_tokens: Maximum token budget cap.
            scopes: Optional scope filters.

        Returns:
            MemoryQueryResult model containing ranked and budgeted memory items.
        """
        # 1. Retrieve
        raw_items = self.retriever.retrieve(context, scopes=scopes)

        # 2. Rank
        search_query = query or context.raw_query
        ranked_items = self.ranker.rank(raw_items, query=search_query)

        # 3. Filter & Budget
        filtered_items = self.filter_engine.filter_and_budget(
            ranked_items,
            max_tokens=max_tokens,
            deduplicate=True,
        )

        if max_results > 0 and len(filtered_items) > max_results:
            filtered_items = filtered_items[:max_results]

        # Calculate total tokens
        total_tokens = sum(
            self.filter_engine.token_estimator.estimate_tokens(item.content)
            for item in filtered_items
        )

        return MemoryQueryResult(
            query=search_query,
            items=filtered_items,
            total_found=len(raw_items),
            token_count=total_tokens,
            metadata={"scopes": [s.value for s in (scopes or list(MemoryScope))]},
        )

    def fetch_memory(self, context: AIContext) -> Dict[str, Any]:
        """Bridge method implementing MemoryProviderInterface for MemoryInjector compatibility.

        Returns formatted dictionary of memory facets.
        """
        query_res = self.query_memories(context, max_results=20)

        facets: Dict[str, List[str]] = {
            "long_term": [],
            "recent": [],
            "preferences": [],
            "pinned": [],
            "execution": [],
        }

        for item in query_res.items:
            facet_key = item.metadata.get("facet")
            if not facet_key or facet_key not in facets:
                facet_key = item.scope.value if hasattr(item.scope, "value") else str(item.scope)
            if facet_key in facets:
                facets[facet_key].append(item.content)
            else:
                facets["long_term"].append(item.content)

        return {
            "long_term": "; ".join(facets["long_term"]) if facets["long_term"] else "None",
            "recent": "; ".join(facets["recent"]) if facets["recent"] else "None",
            "preferences": "; ".join(facets["preferences"]) if facets["preferences"] else "None",
            "pinned": "; ".join(facets["pinned"]) if facets["pinned"] else "None",
            "execution": "; ".join(facets["execution"]) if facets["execution"] else "None",
        }
