"""Unit tests for ContextWindowManager."""

# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
from memory import (
    MemoryEntry,
    MemoryMetadata,
    MemoryType,
    AssistantContext,
    ContextWindowConfig,
)
from memory.manager.context_window_manager import ContextWindowManager


def test_token_estimation() -> None:
    """Verify lightweight token estimation counts characters correctly."""
    manager = ContextWindowManager()
    
    # 4 characters = 1 token
    assert manager.estimate_tokens("abcd") == 1
    assert manager.estimate_tokens("abcdefgh") == 2
    assert manager.estimate_tokens("") == 0
    
    entry = MemoryEntry(
        id="test",
        content="Hello World",  # 11 chars -> 3 tokens
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(additional_info={"session_id": "123"}) # str() = ~20 chars -> ~5 tokens
    )
    tokens = manager.estimate_entry_tokens(entry)
    assert tokens > 3


def test_budget_enforcement_and_pruning() -> None:
    """Verify that optional items are pruned (executions pruned first) to fit budget."""
    config = ContextWindowConfig(
        token_budget=50,  # Small budget
        reserved_response_tokens=10,
        safety_margin_tokens=5,
        minimum_recent_conversations=1,
    )
    # Available budget = 50 - 15 = 35 tokens (~140 chars)
    manager = ContextWindowManager(config=config)
    now = datetime.now(timezone.utc)
    
    # Create entries
    current_context = MemoryEntry(
        id="ctx",
        content="active_workspace",  # ~4 tokens
        memory_type=MemoryType.SESSION,
        metadata=MemoryMetadata(created_at=now)
    )
    
    # Conversations (ordered chronologically)
    c1 = MemoryEntry(
        id="c1",
        content="first message in conversation history",  # ~38 chars -> ~10 tokens
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now - timedelta(minutes=5))
    )
    c2 = MemoryEntry(
        id="c2",
        content="second message in conversation history",  # ~39 chars -> ~10 tokens
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now - timedelta(minutes=1))
    )
    
    # Executions (large content)
    e1 = MemoryEntry(
        id="e1",
        content="execution log with a lot of text detail and traces" * 5,  # huge -> ~65 tokens
        memory_type=MemoryType.ACTIVITY,
        metadata=MemoryMetadata(created_at=now)
    )
    
    raw_ctx = AssistantContext(
        recent_conversations=[c1, c2],  # c2 is the most recent (protected if minimum is 1)
        recent_executions=[e1],
        current_context=current_context,
        preferences=[],
        workspace_context=None,
    )
    
    optimized = manager.optimize_context_window(raw_ctx)
    
    # Executions should be dropped completely because e1 is huge and not mandatory
    assert len(optimized.recent_executions) == 0
    # Mandatory current_context should be kept
    assert optimized.current_context is not None
    # Minimum recent conversation (c2) should be protected
    assert c2 in optimized.recent_conversations


def test_mandatory_memories_preserved() -> None:
    """Verify current context and minimum conversations are preserved regardless of budget tightness."""
    config = ContextWindowConfig(
        token_budget=10,  # Extremely tiny budget (exceeded by mandatory items)
        reserved_response_tokens=5,
        safety_margin_tokens=5,
        minimum_recent_conversations=1,
    )
    manager = ContextWindowManager(config=config)
    now = datetime.now(timezone.utc)
    
    current_context = MemoryEntry(
        id="ctx",
        content="workspace_path",
        memory_type=MemoryType.SESSION,
        metadata=MemoryMetadata(created_at=now)
    )
    
    c1 = MemoryEntry(
        id="c1",
        content="conversation turn",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now)
    )
    
    raw_ctx = AssistantContext(
        recent_conversations=[c1],
        recent_executions=[],
        current_context=current_context,
        preferences=[],
        workspace_context=None,
    )
    
    optimized = manager.optimize_context_window(raw_ctx)
    
    # Exceeded budget but mandatory items MUST remain intact
    assert optimized.current_context is not None
    assert len(optimized.recent_conversations) == 1


def test_chronological_sorting() -> None:
    """Verify that kept conversations are sorted chronologically (oldest to newest)."""
    manager = ContextWindowManager()
    now = datetime.now(timezone.utc)
    
    c1 = MemoryEntry(
        id="c1",
        content="oldest turn",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now - timedelta(hours=2))
    )
    c2 = MemoryEntry(
        id="c2",
        content="middle turn",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now - timedelta(hours=1))
    )
    c3 = MemoryEntry(
        id="c3",
        content="newest turn",
        memory_type=MemoryType.CONVERSATION,
        metadata=MemoryMetadata(created_at=now)
    )
    
    # Input has jumbled/ranked order
    raw_ctx = AssistantContext(
        recent_conversations=[c3, c1, c2],
        recent_executions=[],
        current_context=None,
        preferences=[],
        workspace_context=None,
    )
    
    optimized = manager.optimize_context_window(raw_ctx)
    
    # Must sort oldest to newest: c1, c2, c3
    assert optimized.recent_conversations == [c1, c2, c3]


def test_empty_context() -> None:
    """Verify behavior when the raw context object is empty."""
    manager = ContextWindowManager()
    raw_ctx = AssistantContext(
        recent_conversations=[],
        recent_executions=[],
        current_context=None,
        preferences=[],
        workspace_context=None,
    )
    
    optimized = manager.optimize_context_window(raw_ctx)
    assert len(optimized.recent_conversations) == 0
    assert len(optimized.recent_executions) == 0
    assert optimized.current_context is None


def test_oversized_context() -> None:
    """Verify trimming occurs on high token volumes."""
    config = ContextWindowConfig(
        token_budget=100,  # limit
        reserved_response_tokens=10,
        safety_margin_tokens=10,
        minimum_recent_conversations=1,
    )
    manager = ContextWindowManager(config=config)
    now = datetime.now(timezone.utc)
    
    # Many execution entries
    execs = [
        MemoryEntry(
            id=f"e_{i}",
            content="execution logs details here " * 5,  # ~30 tokens each
            memory_type=MemoryType.ACTIVITY,
            metadata=MemoryMetadata(created_at=now)
        ) for i in range(10)
    ]
    
    raw_ctx = AssistantContext(
        recent_conversations=[],
        recent_executions=execs,
        current_context=None,
        preferences=[],
        workspace_context=None,
    )
    
    optimized = manager.optimize_context_window(raw_ctx)
    
    # It must trim executions to fit available budget of 80 tokens (~2 items)
    assert len(optimized.recent_executions) < 10
    assert len(optimized.recent_executions) > 0


def test_multiple_strategies_placeholders() -> None:
    """Verify that multiple truncation strategies parse configuration safely."""
    config_lod = ContextWindowConfig(truncation_strategy="level_of_detail")
    config_suf = ContextWindowConfig(truncation_strategy="truncation_suffix")
    
    manager_lod = ContextWindowManager(config=config_lod)
    manager_suf = ContextWindowManager(config=config_suf)
    
    assert manager_lod.config.truncation_strategy == "level_of_detail"
    assert manager_suf.config.truncation_strategy == "truncation_suffix"
