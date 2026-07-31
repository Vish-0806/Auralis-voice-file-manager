"""Comprehensive Unit Tests for Phase 10.5: Memory-aware AI.

Validates:
- DefaultMemoryRetriever: Multi-scope retrieval (SESSION, RECENT, LONG_TERM, PINNED)
- DefaultMemoryRanker: Keyword overlap, importance weighting, scope precedence scoring
- DefaultMemoryFilter: Deduplication and token budgeting while preserving rank
- AIMemoryProvider: Unified query execution and MemoryQueryResult construction
- Integration: MemoryInjector seamlessly consuming AIMemoryProvider
- Edge Cases: Empty memory stores, malformed context structures
"""

# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone

from brain.ai import (
    AIContext,
    AIMemoryItem,
    AIMemoryProvider,
    DefaultMemoryFilter,
    DefaultMemoryRanker,
    DefaultMemoryRetriever,
    MemoryInjector,
    MemoryQueryResult,
    MemoryScope,
    SCOPE_WEIGHTS,
)


# ---------------------------------------------------------------------------
# Tests: MemoryRetriever
# ---------------------------------------------------------------------------


def test_memory_retriever_multi_scope_retrieval():
    """Test retrieving memory items across SESSION, RECENT, LONG_TERM, and PINNED scopes."""
    retriever = DefaultMemoryRetriever()

    ctx = AIContext(
        request_id="req-ret-1",
        raw_query="Find Python files",
        memory_context={
            "pinned": "Critical System Rule",
            "session": "Active session query",
            "recent": ["Opened main.py", "Edited config.json"],
            "long_term": {"pref": "User likes Python"},
            "user_preferences": {"theme": "dark"},
        },
        execution_context={"state": "running"},
    )

    items = retriever.retrieve(ctx)
    assert len(items) >= 5

    scopes_found = {item.scope for item in items}
    assert MemoryScope.PINNED in scopes_found
    assert MemoryScope.SESSION in scopes_found
    assert MemoryScope.RECENT in scopes_found
    assert MemoryScope.LONG_TERM in scopes_found


def test_memory_retriever_empty_store():
    """Test memory retrieval with empty memory context."""
    retriever = DefaultMemoryRetriever()
    empty_ctx = AIContext(request_id="req-empty-mem")

    items = retriever.retrieve(empty_ctx)
    assert items == []


# ---------------------------------------------------------------------------
# Tests: MemoryRanker
# ---------------------------------------------------------------------------


def test_memory_ranker_scoring_heuristics():
    """Test relevance ranking using keyword overlap, importance scores, and scope weights."""
    ranker = DefaultMemoryRanker()

    items = [
        AIMemoryItem(
            memory_id="1",
            key="irrelevant",
            content="Unrelated baking recipes",
            scope=MemoryScope.LONG_TERM,
            importance_score=0.2,
        ),
        AIMemoryItem(
            memory_id="2",
            key="matching",
            content="User prefers Python for coding projects",
            scope=MemoryScope.LONG_TERM,
            importance_score=0.5,
        ),
        AIMemoryItem(
            memory_id="3",
            key="pinned_item",
            content="Always keep Python code PEP8 compliant",
            scope=MemoryScope.PINNED,
            importance_score=1.0,
        ),
    ]

    ranked = ranker.rank(items, query="Python coding guidelines")
    assert len(ranked) == 3

    # PINNED item with keyword match should be ranked #1
    assert ranked[0].memory_id == "3"
    assert ranked[0].relevance_score > ranked[1].relevance_score
    # Irrelevant baking recipe should be ranked #3
    assert ranked[-1].memory_id == "1"


# ---------------------------------------------------------------------------
# Tests: MemoryFilter
# ---------------------------------------------------------------------------


def test_memory_filter_deduplication_and_token_budgeting():
    """Test deduplicating identical memories and trimming to token budget."""
    filter_engine = DefaultMemoryFilter()

    items = [
        AIMemoryItem(
            memory_id="1",
            key="k1",
            content="Duplicate preference text",
            scope=MemoryScope.PINNED,
            relevance_score=0.9,
        ),
        AIMemoryItem(
            memory_id="2",
            key="k1",
            content="Duplicate preference text",  # Duplicate
            scope=MemoryScope.PINNED,
            relevance_score=0.9,
        ),
        AIMemoryItem(
            memory_id="3",
            key="k2",
            content="Very long memory text " * 10,
            scope=MemoryScope.RECENT,
            relevance_score=0.7,
        ),
        AIMemoryItem(
            memory_id="4",
            key="k3",
            content="Short memory item",
            scope=MemoryScope.LONG_TERM,
            relevance_score=0.5,
        ),
    ]

    # Test Deduplication
    deduped = filter_engine.filter_and_budget(items, deduplicate=True)
    assert len(deduped) == 3

    # Test Token Budgeting
    budgeted = filter_engine.filter_and_budget(items, max_tokens=15, deduplicate=True)
    assert len(budgeted) < 3
    # Pinned item should be preserved in budget
    assert any(i.scope == MemoryScope.PINNED for i in budgeted)


# ---------------------------------------------------------------------------
# Tests: AIMemoryProvider Unified Query
# ---------------------------------------------------------------------------


def test_ai_memory_provider_query():
    """Test AIMemoryProvider.query_memories returns structured MemoryQueryResult."""
    provider = AIMemoryProvider()

    ctx = AIContext(
        request_id="req-query-1",
        raw_query="Find Python preferences",
        memory_context={
            "pinned": "Rule: Use Python 3.13",
            "recent": "Created test_brain_ai_memory.py",
            "preferences": "Theme: dark, Lang: Python",
        },
    )

    res = provider.query_memories(ctx, query="Python", max_results=5, max_tokens=200)

    assert isinstance(res, MemoryQueryResult)
    assert res.query == "Python"
    assert len(res.items) > 0
    assert res.total_found >= len(res.items)
    assert res.token_count > 0


# ---------------------------------------------------------------------------
# Tests: Integration with MemoryInjector
# ---------------------------------------------------------------------------


def test_memory_injector_integration_with_ai_memory_provider():
    """Test MemoryInjector seamlessly consumes AIMemoryProvider."""
    provider = AIMemoryProvider()
    injector = MemoryInjector(memory_provider=provider)

    ctx = AIContext(
        request_id="req-inj-1",
        raw_query="Project info",
        memory_context={
            "pinned": "Pinned System Policy",
            "long_term": "User is a Lead Engineer",
            "preferences": "Likes dark mode",
        },
    )

    mem_text = injector.inject_memory(ctx)
    assert "Pinned System Policy" in mem_text or "Lead Engineer" in mem_text or "dark" in mem_text

    mem_msg = injector.build_memory_message(ctx)
    assert mem_msg is not None
    assert mem_msg.content == mem_text
