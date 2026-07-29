"""Unit tests for ConversationContextManager (Phase 9.1.2)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.conversation.context_manager import (
    ConversationContext,
    ConversationContextConfig,
    ConversationContextManager,
)
from brain.conversation.conversation_session import ConversationTurn


@pytest.fixture
def manager() -> ConversationContextManager:
    """Fixture providing a fresh ConversationContextManager instance."""
    return ConversationContextManager()


def test_create_context(manager: ConversationContextManager) -> None:
    """Verifies successful creation of a context with default window size."""
    ctx = manager.create_context(session_id="session_101", metadata={"client": "web"})

    assert ctx.session_id == "session_101"
    assert ctx.context_window == []
    assert ctx.max_context_turns == manager.config.default_context_window
    assert ctx.metadata == {"client": "web"}
    assert isinstance(ctx.last_updated, datetime)


def test_retrieve_context(manager: ConversationContextManager) -> None:
    """Verifies context retrieval by session_id."""
    manager.create_context(session_id="session_101")
    ctx = manager.get_context("session_101")

    assert ctx is not None
    assert ctx.session_id == "session_101"


def test_append_turns(manager: ConversationContextManager) -> None:
    """Verifies appending turns to context window."""
    manager.create_context(session_id="session_101")
    t1 = ConversationTurn(turn_id="t1", role="user", content="Hello")
    t2 = ConversationTurn(turn_id="t2", role="assistant", content="Hi there")

    updated = manager.append_turn("session_101", t1)
    assert len(updated.context_window) == 1

    updated2 = manager.append_turn("session_101", t2)
    assert len(updated2.context_window) == 2
    assert updated2.context_window[1].turn_id == "t2"


def test_ordering(manager: ConversationContextManager) -> None:
    """Verifies turns in context window maintain strict chronological order."""
    manager.create_context(session_id="session_101")
    t1 = ConversationTurn(turn_id="t1", role="user", content="1")
    t2 = ConversationTurn(turn_id="t2", role="assistant", content="2")
    t3 = ConversationTurn(turn_id="t3", role="user", content="3")

    manager.append_turn("session_101", t1)
    manager.append_turn("session_101", t2)
    manager.append_turn("session_101", t3)

    recent = manager.get_recent_turns("session_101")
    assert [t.turn_id for t in recent] == ["t1", "t2", "t3"]

    # Test limit parameter
    recent_2 = manager.get_recent_turns("session_101", limit=2)
    assert [t.turn_id for t in recent_2] == ["t2", "t3"]


def test_context_window_enforcement(manager: ConversationContextManager) -> None:
    """Verifies sliding context window discards oldest turns when cap exceeded."""
    manager.create_context(session_id="session_101", max_context_turns=3)

    for i in range(5):
        turn = ConversationTurn(turn_id=f"t{i}", role="user", content=f"msg {i}")
        manager.append_turn("session_101", turn)

    ctx = manager.get_context("session_101")
    assert len(ctx.context_window) == 3
    # Oldest (t0, t1) should be discarded; t2, t3, t4 remain
    assert [t.turn_id for t in ctx.context_window] == ["t2", "t3", "t4"]


def test_resize_larger(manager: ConversationContextManager) -> None:
    """Verifies expanding the context window cap."""
    manager.create_context(session_id="session_101", max_context_turns=2)
    for i in range(2):
        manager.append_turn("session_101", ConversationTurn(turn_id=f"t{i}", role="user", content=str(i)))

    resized = manager.resize_context_window("session_101", new_max_turns=5)
    assert resized.max_context_turns == 5

    manager.append_turn("session_101", ConversationTurn(turn_id="t2", role="user", content="2"))
    assert len(manager.get_context("session_101").context_window) == 3


def test_resize_smaller(manager: ConversationContextManager) -> None:
    """Verifies reducing context window cap discards oldest turns immediately."""
    manager.create_context(session_id="session_101", max_context_turns=5)
    for i in range(5):
        manager.append_turn("session_101", ConversationTurn(turn_id=f"t{i}", role="user", content=str(i)))

    resized = manager.resize_context_window("session_101", new_max_turns=2)
    assert resized.max_context_turns == 2
    assert [t.turn_id for t in resized.context_window] == ["t3", "t4"]


def test_metadata_merge(manager: ConversationContextManager) -> None:
    """Verifies updating context metadata merges keys properly."""
    manager.create_context(session_id="session_101", metadata={"a": 1, "b": 2})

    updated = manager.update_context("session_101", metadata={"b": 99, "c": 3})
    assert updated.metadata == {"a": 1, "b": 99, "c": 3}


def test_timestamps(manager: ConversationContextManager) -> None:
    """Verifies last_updated timestamp updates on context operations."""
    ctx = manager.create_context(session_id="session_101")
    t0 = ctx.last_updated

    turn = ConversationTurn(turn_id="t1", role="user", content="hi")
    updated = manager.append_turn("session_101", turn)
    assert updated.last_updated >= t0


def test_expiration(manager: ConversationContextManager) -> None:
    """Verifies inactive contexts are expired past timeout."""
    mgr = ConversationContextManager()
    ctx = mgr.create_context(session_id="session_101")

    # Manually backdate timestamp
    mgr._contexts["session_101"] = ConversationContext(
        session_id=ctx.session_id,
        context_window=ctx.context_window,
        max_context_turns=ctx.max_context_turns,
        last_updated=datetime.now(timezone.utc) - timedelta(seconds=7200),
        metadata=ctx.metadata,
    )

    expired = mgr.expire_contexts(timeout_seconds=3600)
    assert "session_101" in expired
    assert mgr.get_context("session_101") is None


def test_removal(manager: ConversationContextManager) -> None:
    """Verifies context removal."""
    manager.create_context(session_id="session_101")

    removed = manager.remove_context("session_101")
    assert removed is True
    assert manager.get_context("session_101") is None


def test_clearing(manager: ConversationContextManager) -> None:
    """Verifies clearing turns from context window."""
    manager.create_context(session_id="session_101")
    manager.append_turn("session_101", ConversationTurn(turn_id="t1", role="user", content="hi"))

    cleared = manager.clear_context("session_101")
    assert cleared is True

    ctx = manager.get_context("session_101")
    assert ctx.context_window == []


def test_list_contexts(manager: ConversationContextManager) -> None:
    """Verifies list_contexts returns all active contexts."""
    manager.create_context(session_id="s1")
    manager.create_context(session_id="s2")

    contexts = manager.list_contexts()
    assert len(contexts) == 2
    assert set(c.session_id for c in contexts) == {"s1", "s2"}


def test_dependency_injection() -> None:
    """Verifies manager honors custom ConversationContextConfig."""
    cfg = ConversationContextConfig(
        default_context_window=5,
        maximum_context_window=10,
        maximum_contexts=2,
        context_timeout_seconds=60,
    )
    mgr = ConversationContextManager(config=cfg)

    c1 = mgr.create_context("s1")
    assert c1.max_context_turns == 5

    mgr.create_context("s2")
    mgr.create_context("s3")
    # Capacity limit maximum_contexts=2 should cause eviction of oldest
    assert len(mgr.list_contexts()) <= 2


def test_thread_safety() -> None:
    """Verifies thread safety under concurrent turn appends."""
    mgr = ConversationContextManager()
    mgr.create_context("s1", max_context_turns=100)

    def append_worker(idx: int) -> None:
        turn = ConversationTurn(turn_id=f"t_{idx}", role="user", content=f"content {idx}")
        mgr.append_turn("s1", turn)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(append_worker, i) for i in range(50)]
        for f in futures:
            f.result()

    ctx = mgr.get_context("s1")
    assert len(ctx.context_window) == 50


def test_invalid_ids(manager: ConversationContextManager) -> None:
    """Verifies unknown session IDs return None / False without raising exceptions."""
    non_existent = "unknown_session_999"

    assert manager.get_context(non_existent) is None
    assert manager.update_context(non_existent) is None
    assert manager.append_turn(non_existent, ConversationTurn(turn_id="t1", role="user", content="hi")) is None
    assert manager.get_recent_turns(non_existent) == []
    assert manager.resize_context_window(non_existent, 10) is None
    assert manager.clear_context(non_existent) is False
    assert manager.remove_context(non_existent) is False


def test_context_snapshot_immutability(manager: ConversationContextManager) -> None:
    """Verifies ConversationContext is immutable snapshot returned to callers."""
    ctx = manager.create_context("s1")

    with pytest.raises((TypeError, ValidationError)):
        ctx.max_context_turns = 50


def test_configuration_limits(manager: ConversationContextManager) -> None:
    """Verifies maximum_context_window hard limit is enforced on creation/resizing."""
    cfg = ConversationContextConfig(maximum_context_window=30)
    mgr = ConversationContextManager(config=cfg)

    ctx = mgr.create_context("s1", max_context_turns=500)
    assert ctx.max_context_turns == 30

    resized = mgr.resize_context_window("s1", new_max_turns=200)
    assert resized.max_context_turns == 30
